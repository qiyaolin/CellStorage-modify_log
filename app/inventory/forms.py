from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, IntegerField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange, Email, URL
from wtforms.widgets import TextArea


class InventoryTypeForm(FlaskForm):
    name = StringField('Type Name', validators=[DataRequired()], 
                      render_kw={'placeholder': 'e.g., Chemical, Antibody, Equipment'})
    description = TextAreaField('Description', validators=[Optional()])
    icon = StringField('Icon Class', validators=[Optional()], 
                      render_kw={'placeholder': 'e.g., fa-flask, fa-vial'})
    custom_fields = TextAreaField('Custom Fields (JSON)', validators=[Optional()],
                                 render_kw={'placeholder': '{"field1": "type", "field2": "type"}'})
    submit = SubmitField('Create Type')


class LocationForm(FlaskForm):
    name = StringField('Location Name', validators=[DataRequired()],
                      render_kw={'placeholder': 'e.g., Room 101, Fridge A'})
    parent_id = SelectField('Parent Location', coerce=int, validators=[Optional()])
    location_type = SelectField('Location Type', 
                               choices=[('room', 'Room'), ('cabinet', 'Cabinet'), 
                                       ('shelf', 'Shelf'), ('freezer', 'Freezer'),
                                       ('fridge', 'Fridge'), ('incubator', 'Incubator'), 
                                       ('bench', 'Bench'), ('drawer', 'Drawer')],
                               validators=[Optional()])
    temperature = StringField('Temperature', validators=[Optional()],
                             render_kw={'placeholder': 'e.g., RT, 4°C, -20°C'})
    description = TextAreaField('Description', validators=[Optional()])
    
    # Capacity management fields
    max_capacity = IntegerField('Maximum Capacity', validators=[Optional(), NumberRange(min=1)],
                               render_kw={'placeholder': 'Leave empty for unlimited'})
    capacity_unit = SelectField('Capacity Unit',
                               choices=[('items', 'Items'), ('mL', 'mL'), ('L', 'L'),
                                       ('mg', 'mg'), ('g', 'g'), ('kg', 'kg'),
                                       ('positions', 'Positions'), ('slots', 'Slots')],
                               default='items')
    
    submit = SubmitField('Create Location')


class SupplierForm(FlaskForm):
    name = StringField('Supplier Name', validators=[DataRequired()],
                      render_kw={'placeholder': 'e.g., Sigma-Aldrich, Thermo Fisher'})
    contact_person = StringField('Contact Person', validators=[Optional()])
    email = StringField('Email', validators=[Optional(), Email()])
    phone = StringField('Phone', validators=[Optional()])
    website = StringField('Website', validators=[Optional(), URL()])
    address = TextAreaField('Address', validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Create Supplier')


class InventoryItemForm(FlaskForm):
    name = StringField('Item Name', validators=[DataRequired()],
                      render_kw={'placeholder': 'e.g., DMEM Medium, Anti-GFP Antibody'})
    description = TextAreaField('Description', validators=[Optional()])
    catalog_number = StringField('Catalog Number', validators=[Optional()],
                                render_kw={'placeholder': 'e.g., D5796'})
    barcode = StringField('Barcode', validators=[Optional()],
                         render_kw={'placeholder': 'Scan or enter barcode'})
    
    type_id = SelectField('Inventory Type', coerce=int, validators=[DataRequired()])
    supplier_id = SelectField('Supplier', coerce=int, validators=[Optional()])
    location_id = SelectField('Location', coerce=int, validators=[Optional()])
    
    current_quantity = FloatField('Current Quantity', validators=[DataRequired(), NumberRange(min=0)],
                                 default=0)
    minimum_quantity = FloatField('Minimum Quantity', validators=[DataRequired(), NumberRange(min=0)],
                                 default=0, render_kw={'placeholder': 'Alert threshold'})
    unit = StringField('Unit', validators=[DataRequired()],
                      render_kw={'placeholder': 'e.g., mL, mg, pieces'})
    
    unit_price = FloatField('Unit Price', validators=[Optional(), NumberRange(min=0)])
    currency = SelectField('Currency', 
                          choices=[('USD', 'USD'), ('EUR', 'EUR'), ('CNY', 'CNY')],
                          default='USD')
    
    expiration_date = DateField('Expiration Date', validators=[Optional()])
    received_date = DateField('Received Date', validators=[Optional()],
                             default=lambda: None)
    
    submit = SubmitField('Create Item')


class OrderForm(FlaskForm):
    supplier_id = SelectField('Supplier', coerce=int, validators=[Optional()])
    needed_by_date = DateField('Needed By Date', validators=[Optional()])
    priority = SelectField('Priority', 
                          choices=[('Low', 'Low'), ('Normal', 'Normal'), 
                                  ('High', 'High'), ('Urgent', 'Urgent')],
                          default='Normal')
    justification = TextAreaField('Justification', validators=[DataRequired()],
                                 render_kw={'placeholder': 'Why is this order needed?'})
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Create Order')


class OrderItemForm(FlaskForm):
    item_name = StringField('Item Name', validators=[DataRequired()])
    catalog_number = StringField('Catalog Number', validators=[Optional()])
    description = TextAreaField('Description', validators=[Optional()])
    quantity_requested = FloatField('Quantity', validators=[DataRequired(), NumberRange(min=0.01)])
    unit = StringField('Unit', validators=[DataRequired()])
    unit_price = FloatField('Unit Price', validators=[Optional(), NumberRange(min=0)])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Add Item')


class UsageForm(FlaskForm):
    quantity_used = FloatField('Quantity Used', validators=[DataRequired(), NumberRange(min=0.01)])
    reason = StringField('Reason', validators=[DataRequired()],
                        render_kw={'placeholder': 'e.g., Experiment, Preparation'})
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Record Usage')


class BulkEditForm(FlaskForm):
    action = SelectField('Action', 
                        choices=[('update_location', 'Update Location'),
                                ('update_status', 'Update Status'),
                                ('adjust_quantity', 'Adjust Quantity')],
                        validators=[DataRequired()])
    location_id = SelectField('New Location', coerce=int, validators=[Optional()])
    status = SelectField('New Status',
                        choices=[('Available', 'Available'), ('Used Up', 'Used Up'),
                                ('Expired', 'Expired'), ('Reserved', 'Reserved')],
                        validators=[Optional()])
    quantity_adjustment = FloatField('Quantity Adjustment', validators=[Optional()])
    reason = StringField('Reason', validators=[Optional()])
    submit = SubmitField('Apply Changes')


class SearchForm(FlaskForm):
    search_term = StringField('Search', render_kw={'placeholder': 'Search items...'})
    type_filter = SelectField('Type', coerce=int, validators=[Optional()])
    location_filter = SelectField('Location', coerce=int, validators=[Optional()])
    status_filter = SelectField('Status', 
                               choices=[('', 'All Statuses'), ('Available', 'Available'),
                                       ('Low Stock', 'Low Stock'), ('Used Up', 'Used Up'),
                                       ('Expired', 'Expired')],
                               validators=[Optional()])
    submit = SubmitField('Search')