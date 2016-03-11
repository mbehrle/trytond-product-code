# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool, PoolMeta
from trytond import backend
from trytond.transaction import Transaction

__all__ = ['Product', 'ProductCode']
__metaclass__ = PoolMeta


class Product:
    "Product"
    __name__ = 'product.product'

    codes = fields.One2Many(
        'product.product.code', 'product', 'Codes'
    )

    @classmethod
    def search_rec_name(cls, name, clause):
        domain = super(Product, cls).search_rec_name(name, clause)
        domain.append(('codes.code', ) + tuple(clause[1:]))
        return domain

    @classmethod
    def copy(cls, products, default=None):
        if default is None:
            default = {}
        default = default.copy()
        default.setdefault('codes', None)
        return super(Product, cls).copy(products, default=default)


class ProductCode(ModelSQL, ModelView):
    "Product Code"
    __name__ = 'product.product.code'
    _rec_name = 'code'

    code = fields.Char('Value', required=True, select=True)
    code_type = fields.Selection([
        ('ean', 'EAN'),
        ('upc-a', 'UPC-A'),
        ('other', 'Other')
    ], 'Type', required=True)
    active = fields.Boolean('Active')
    product = fields.Many2One(
        'product.product', 'Product', ondelete='CASCADE', select=True,
        required=True
    )

    @classmethod
    def __setup__(cls):
        super(ProductCode, cls).__setup__()
        cls._error_messages.update({
            'wrong_code_length_ean': 'Wrong code length:'
            '\nFor EAN, length should be 13.',
            'wrong_code_length_upc': 'Wrong code length:'
            '\nFor UPC-A, length should be 12.',
            'code_unique': 'Duplicate code:'
            '\nThe code "%(code)s" with type "%(code_type)s" already exists.',
        })

    @classmethod
    def __register__(cls, module_name):
        TableHandler = backend.get('TableHandler')
        cursor = Transaction().cursor

        super(ProductCode, cls).__register__(module_name)

        table = TableHandler(cursor, cls, module_name)
        # Migration from 3.4: Drop sql constraint in favor of validate
        table.drop_constraint('code_uniq')

    @classmethod
    def validate(cls, records):
        super(ProductCode, cls).validate(records)
        cls.check_code(records)

    @classmethod
    def check_code(cls, records):
        '''
        Check the code length and uniqueness:
        EAN should be 13 characters and unique
        UPC-A should be 12 characters and unique
        '''
        for record in records:
            if record.code_type == 'ean' and len(record.code) != 13:
                record.raise_user_error('wrong_code_length_ean')
            if record.code_type == 'upc-a' and len(record.code) != 12:
                record.raise_user_error('wrong_code_length_upc')
            for type in ['ean', 'upc-a']:
                codes = cls.search([
                        ('id', '!=', record.id),
                        ('code', '=', record.code),
                        ('code_type', '=', type),
                        ])
                if codes:
                    cls.raise_user_error('code_unique', {
                            'code': record.code,
                            'code_type': record.code_type,
                            })

    @staticmethod
    def default_active():
        return True
