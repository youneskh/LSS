import numpy as np
from odoo import models, fields, api


class DataAnalysis(models.Model):
    _name = 'data.analysis'
    _description = 'Data Analysis with Numpy'

    name = fields.Char(string='Analysis Name', required=True)
    description = fields.Text()
    data_values = fields.Text(string='Data Values (comma-separated numbers)', help='Enter numbers separated by commas')

    # Computed fields for numpy analysis
    mean_value = fields.Float(string='Mean', compute='_compute_statistics', store=False)
    std_dev = fields.Float(string='Standard Deviation', compute='_compute_statistics', store=False)
    min_value = fields.Float(compute='_compute_statistics', store=False)
    max_value = fields.Float(compute='_compute_statistics', store=False)
    median_value = fields.Float(string='Median', compute='_compute_statistics', store=False)

    @api.depends('data_values')
    def _compute_statistics(self):
        for record in self:
            if record.data_values:
                try:
                    # Parse comma-separated values into numpy array
                    values = np.array([float(x.strip()) for x in record.data_values.split(',') if x.strip()])

                    if len(values) > 0:
                        record.mean_value = float(np.mean(values))
                        record.std_dev = float(np.std(values))
                        record.min_value = float(np.min(values))
                        record.max_value = float(np.max(values))
                        record.median_value = float(np.median(values))
                    else:
                        record.mean_value = 0
                        record.std_dev = 0
                        record.min_value = 0
                        record.max_value = 0
                        record.median_value = 0
                except (ValueError, TypeError):
                    record.mean_value = 0
                    record.std_dev = 0
                    record.min_value = 0
                    record.max_value = 0
                    record.median_value = 0
            else:
                record.mean_value = 0
                record.std_dev = 0
                record.min_value = 0
                record.max_value = 0
                record.median_value = 0
