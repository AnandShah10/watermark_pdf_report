from odoo import fields, models, api, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    watermark_active = fields.Boolean(string="PDF report with watermark", default=False)
    watermark_type = fields.Selection([('image', 'Image/PDF'), ('text', 'Text')],
                                      string="Watermark Type")
    watermark_position = fields.Selection([('center', 'Center'), ('custom', 'Custom')])

    # Text Watermark Fields
    watermark_text = fields.Char(string="Watermark Text")
    watermark_rotation = fields.Integer(string="Rotation (deg)")
    watermark_fontsize = fields.Integer(string="Font Size (px)")
    watermark_color = fields.Char(string="Color")
    watermark_opacity = fields.Float(string="Opacity")

    # Image Watermark Fields
    watermark_image = fields.Binary(string="Watermark Image/PDF")
    watermark_height = fields.Integer(string="Height (px)")
    watermark_width = fields.Integer(string="Width (px)")
    watermark_image_opacity = fields.Float(string="Opacity")

    # Custom Position Fields
    margin_bottom = fields.Integer(string="Margin Bottom (px)")
    margin_left = fields.Integer(string="Margin Left (px)")

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        IrConfigParam = self.env['ir.config_parameter'].sudo()
        IrConfigParam.set_param('watermark_pdf_report.watermark_active', self.watermark_active)
        IrConfigParam.set_param('watermark_pdf_report.watermark_type', self.watermark_type)
        IrConfigParam.set_param('watermark_pdf_report.watermark_position', self.watermark_position)
        IrConfigParam.set_param('watermark_pdf_report.watermark_text', self.watermark_text)
        IrConfigParam.set_param('watermark_pdf_report.watermark_rotation', self.watermark_rotation)
        IrConfigParam.set_param('watermark_pdf_report.watermark_fontsize', self.watermark_fontsize)
        IrConfigParam.set_param('watermark_pdf_report.watermark_color', self.watermark_color)
        IrConfigParam.set_param('watermark_pdf_report.watermark_opacity', self.watermark_opacity)
        IrConfigParam.set_param('watermark_pdf_report.watermark_image', self.watermark_image)
        IrConfigParam.set_param('watermark_pdf_report.watermark_height', self.watermark_height)
        IrConfigParam.set_param('watermark_pdf_report.watermark_width', self.watermark_width)
        IrConfigParam.set_param('watermark_pdf_report.watermark_image_opacity', self.watermark_image_opacity)
        IrConfigParam.set_param('watermark_pdf_report.margin_bottom', self.margin_bottom)
        IrConfigParam.set_param('watermark_pdf_report.margin_left', self.margin_left)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        IrConfigParam = self.env['ir.config_parameter'].sudo()
        res.update(
            watermark_active=IrConfigParam.get_param('watermark_pdf_report.watermark_active', default=False),
            watermark_type=IrConfigParam.get_param('watermark_pdf_report.watermark_type', default='text'),
            watermark_position=IrConfigParam.get_param('watermark_pdf_report.watermark_position', default='center'),
            watermark_text=IrConfigParam.get_param('watermark_pdf_report.watermark_text', default=''),
            watermark_rotation=IrConfigParam.get_param('watermark_pdf_report.watermark_rotation', default=0),
            watermark_fontsize=IrConfigParam.get_param('watermark_pdf_report.watermark_fontsize', default=12),
            watermark_color=IrConfigParam.get_param('watermark_pdf_report.watermark_color', default='#000000'),
            watermark_opacity=IrConfigParam.get_param('watermark_pdf_report.watermark_opacity', default=0.1),
            watermark_image=IrConfigParam.get_param('watermark_pdf_report.watermark_image', default=False),
            watermark_height=IrConfigParam.get_param('watermark_pdf_report.watermark_height', default=100),
            watermark_width=IrConfigParam.get_param('watermark_pdf_report.watermark_width', default=100),
            watermark_image_opacity=IrConfigParam.get_param('watermark_pdf_report.watermark_image_opacity',
                                                            default=0.1),
            margin_bottom=IrConfigParam.get_param('watermark_pdf_report.margin_bottom', default=0),
            margin_left=IrConfigParam.get_param('watermark_pdf_report.margin_left', default=0),
        )
        return res

    @api.onchange('module_watermark_active')
    def _onchange_module_watermark_active(self):
        if not self.module_watermark_active:
            self.watermark_type = False
            self.watermark_position = False

    @api.onchange('watermark_type')
    def _onchange_watermark_type(self):
        if self.watermark_type == 'text':
            self.watermark_image = False
            self.watermark_height = False
            self.watermark_width = False
        elif self.watermark_type == 'image':
            self.watermark_text = False
            self.watermark_rotation = False
            self.watermark_fontsize = False
            self.watermark_color = False
            self.watermark_opacity = False

    @api.onchange('watermark_position')
    def _onchange_watermark_position(self):
        if self.watermark_position == 'center':
            self.margin_bottom = False
            self.margin_left = False
