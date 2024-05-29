from base64 import b64decode
from io import BytesIO
from logging import getLogger
from PIL import Image, ImageEnhance
from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval
from PyPDF2 import PdfFileReader, PdfFileWriter, PdfFileMerger
from PyPDF2.utils import PdfReadError
from PIL import PdfImagePlugin
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

logger = getLogger(__name__)


class Report(models.Model):
    _inherit = "ir.actions.report"

    def hex_to_rgb(self, hex_color):
        """Converts hex color to RGB."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i + 2], 16) / 255.0 for i in (0, 2, 4))

    def named_color_to_rgb(self, color_name):
        """Converts named color to RGB."""
        from reportlab.lib import colors  # Import directly from reportlab.lib
        color_obj = colors.toColor(color_name)
        if isinstance(color_obj, tuple):
            return color_obj[0] / 255.0, color_obj[1] / 255.0, color_obj[2] / 255.0
        else:
            # Handle non-tuple case (e.g., named color)
            return color_obj.red / 255.0, color_obj.green / 255.0, color_obj.blue / 255.0

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        if not self.env.context.get("res_ids"):
            return super(Report, self.with_context(res_ids=res_ids))._render_qweb_pdf(
                report_ref, res_ids=res_ids, data=data
            )
        return super(Report, self)._render_qweb_pdf(
            report_ref, res_ids=res_ids, data=data
        )

    def pdf_has_usable_pages(self, numpages):
        if numpages < 1:
            logger.error("Your watermark pdf does not contain any pages")
            return False
        if numpages > 1:
            logger.debug(
                "Your watermark pdf contains more than one page, "
                "all but the first one will be ignored"
            )
        return True

    @api.model
    def _run_wkhtmltopdf(
            self,
            bodies,
            report_ref=False,
            header=None,
            footer=None,
            landscape=False,
            specific_paperformat_args=None,
            set_viewport_size=False,
    ):
        print(bodies, report_ref,
              'Working or not ???????????????????????????????????????????????????????')
        # mod_bodies = self.modify_html(str(bodies))
        # print(bodies, 'Newbody.............................................................')
        result = super(Report, self)._run_wkhtmltopdf(
            bodies,
            report_ref=report_ref,
            header=header,
            footer=footer,
            landscape=landscape,
            specific_paperformat_args=specific_paperformat_args,
            set_viewport_size=set_viewport_size,
        )
        docids = self.env.context.get("res_ids", False)
        report_sudo = self._get_report(report_ref)
        watermark = None
        x, y = 0, 0
        conf = self.env['res.config.settings'].get_values()
        if not conf.get('watermark_active'):
            return result
        if conf.get('watermark_type') == 'image':
            watermark_image = conf.get('watermark_image')
            if isinstance(watermark_image, str):
                watermark = b64decode(watermark_image)
            else:
                logger.error("Watermark image is not a valid base64 string")
                return result
            pdf = PdfFileWriter()
            pdf_watermark = None
            try:
                pdf_watermark = PdfFileReader(BytesIO(watermark))
            except PdfReadError:
                # let's see if we can convert this with pillow
                try:
                    image_width = int(conf.get('watermark_width', 100))
                    image_height = int(conf.get('watermark_height', 100))
                    opacity = float(conf.get('watermark_image_opacity', 0.5))
                    Image.init()
                    image = Image.open(BytesIO(watermark))
                    image = image.resize((image_width, image_height), Image.ANTIALIAS)
                    if not 0 <= opacity <= 1:
                        logger.error("Opacity value should be between 0 and 1")
                        return result
                    if image.mode != 'RGBA':
                        image = image.convert('RGBA')
                    else:
                        image = image.copy()
                    alpha = image.split()[3]
                    print("Alpha,,,,,,,,,,,,", alpha)
                    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
                    print("Alfa.............", alpha)
                    image.putalpha(alpha)
                    _rgb = Image.new('RGB', image.size, (255, 255, 255))
                    _rgb.paste(image, mask=image.split()[3])
                    print("image", _rgb)
                    image = _rgb
                    pdf_buffer = BytesIO()
                    resolution = image.info.get("dpi", self.paperformat_id.dpi or 100)
                    if isinstance(resolution, tuple):
                        resolution = resolution[0]
                    image.save(pdf_buffer, "pdf", resolution=resolution)
                    pdf_watermark = PdfFileReader(pdf_buffer)
                except Exception as e:
                    logger.exception("Failed to load watermark", e)

            if not pdf_watermark:
                logger.error("No usable watermark found, got %s...", watermark[:100])
                return result

            if not self.pdf_has_usable_pages(pdf_watermark.numPages):
                return result

            for page in PdfFileReader(BytesIO(result)).pages:
                watermark_page = pdf.addBlankPage(
                    page.mediaBox.getWidth(), page.mediaBox.getHeight()
                )
                wm_width = pdf_watermark.getPage(0).mediaBox.getWidth()
                wm_height = pdf_watermark.getPage(0).mediaBox.getHeight()
                # Calculate position
                if conf.get('watermark_position') == 'center':
                    # Center alignment
                    x = (page.mediaBox.getWidth() - wm_width) / 2
                    y = (page.mediaBox.getHeight() - wm_height) / 2
                elif conf.get('watermark_position') == 'custom':
                    # Custom margins
                    x = float(conf.get('margin_left', 0))
                    y = float(conf.get('margin_bottom', 0))
                watermark_page.mergeTranslatedPage(pdf_watermark.getPage(0), x, y)
                watermark_page.mergePage(page)

            pdf_content = BytesIO()
            pdf.write(pdf_content)

            return pdf_content.getvalue()
        elif conf.get('watermark_active') and conf.get('watermark_type') == 'text' and conf.get('watermark_text'):
            watermark_buffer = BytesIO()
            c = canvas.Canvas(watermark_buffer, pagesize=letter)
            c.setFont("Helvetica", int(conf.get('watermark_fontsize', 12)))
            color = conf.get('watermark_color', '#000000')
            if color.startswith('#'):
                color = self.hex_to_rgb(color)
            else:
                color = self.named_color_to_rgb(color)
            c.setFillColorRGB(*color)
            opacity = float(conf.get('watermark_opacity', 0.1))  # Convert to float
            if opacity < 0 or opacity > 1:
                opacity = 0.1  # Set default opacity if invalid value provided
            c.setFillAlpha(opacity)
            rotation_angle = int(conf.get('watermark_rotation', 45))
            if not isinstance(rotation_angle, (int, float)):
                rotation_angle = 45  # Set default rotation angle if invalid value provided
            if conf.get('watermark_position') == 'center':
                # Calculate position for center alignment
                page_width, page_height = letter
                text_width = c.stringWidth(conf.get('watermark_text'))
                y = (page_width / 2) - text_width
                x = page_height / 2
            elif conf.get('watermark_position') == 'custom':
                # Use margins for custom position
                x = float(conf.get('margin_left', 0))
                y = float(conf.get('margin_bottom', 0))
            c.saveState()
            print("Roation..................", rotation_angle)
            c.rotate(rotation_angle)
            watermark_text = conf.get('watermark_text', '')
            print("Watermark text $$$$$$$$$$$", watermark_text)
            if watermark_text:
                c.drawString(x, y, watermark_text)
                c.save()
            print('canvas@@@@@@@@@@@@@@', c)
            if watermark_buffer.tell() == 0:
                # Handle the case of an empty watermark PDF
                logger.exception("Watermark PDF buffer is empty")
                return result
                # Reset the watermark PDF buffer's file pointer to the beginning
            watermark_buffer.seek(0)
            # Attempt to read the watermark PDF
            try:
                watermark_pdf = PdfFileReader(watermark_buffer)
                if not watermark_pdf:
                    logger.error("Failed to generate text watermark")
                    return result

                if not self.pdf_has_usable_pages(watermark_pdf.numPages):
                    return result
                pdf = PdfFileWriter()
                for page in PdfFileReader(BytesIO(result)).pages:
                    watermark_page = pdf.addBlankPage(
                        page.mediaBox.getWidth(), page.mediaBox.getHeight()
                    )
                    watermark_page.mergePage(watermark_pdf.getPage(0))
                    watermark_page.mergePage(page)
                pdf_content = BytesIO()
                pdf.write(pdf_content)
                return pdf_content.getvalue()
            except PdfReadError as e:
                # Handle the case of an unreadable PDF
                logger.exception("Failed to read watermark PDF:", e)
                return result
        else:
            return result
