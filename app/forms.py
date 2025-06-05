from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    SubmitField,
    SelectField,
    IntegerField,
    FloatField,
    DateField,
    TextAreaField,
    SelectMultipleField,
    FileField,
    widgets,
)
from wtforms.validators import (
    DataRequired,
    EqualTo,
    Length,
    ValidationError,
    Optional,
    NumberRange,
)
from flask_wtf import FlaskForm
from app.models import User, CellLine, Box


class MultiCheckboxField(SelectMultipleField):
    """Render a list of checkboxes."""
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

def coerce_int_or_none(x):
    """
    Coerces a value to an integer if possible, or returns None if it's an empty string.
    Raises ValueError for other non-integer-coercible values to maintain strictness.
    """
    if x == "": # Handle the empty string from the placeholder option
        return None
    if x is None:
        return None
    try:
        return int(x)
    except ValueError:
        # Re-raise for values that are not empty string but still not int,
        # if strict checking is desired for non-empty, non-int values.
        # Or, for a more lenient approach, you could return None here too.
        # For a SelectField, values should generally match choice keys.
        raise ValueError(f"Cannot coerce '{x}' to int unless it's an empty string for 'None'")
    except TypeError: # for example, if x is a list or dict
         raise TypeError(f"Cannot coerce type '{type(x)}' to int")

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=1, max=64)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class UserCreationForm(FlaskForm): # For admin to create users
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match.')])
    role = SelectField('Role', choices=[('user', 'User'), ('admin', 'Admin')], validators=[DataRequired()])
    submit = SubmitField('Create User')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('This username is already taken. Please choose a different one.')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match.')])
    submit = SubmitField('Change Password')

class CellLineForm(FlaskForm):
    name = StringField('Cell Line Name', validators=[DataRequired(), Length(max=128)])
    source = StringField('Source (e.g., ATCC, Gift)', validators=[Optional(), Length(max=128)])
    species = StringField('Species (e.g., Human, Mouse)', validators=[Optional(), Length(max=64)])
    original_passage = StringField('Original Passage No.', validators=[Optional(), Length(max=64)])
    culture_medium = StringField('Culture Medium', validators=[Optional(), Length(max=255)])
    antibiotic_resistance = StringField('Antibiotic Resistance', validators=[Optional(), Length(max=255)])
    growth_properties = TextAreaField('Growth Properties (e.g., Adherent, Suspension)', validators=[Optional()])
    mycoplasma_status = StringField('Mycoplasma Status (e.g., Negative (YYYY-MM-DD))', validators=[Optional(), Length(max=64)])
    date_established = DateField('Date Established/Received (YYYY-MM-DD)', format='%Y-%m-%d', validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save Cell Line')

class TowerForm(FlaskForm):
    name = StringField('Tower Name/Identifier', validators=[DataRequired(), Length(max=64)])
    freezer_name = StringField('Associated Freezer (e.g., -80C Fridge A)', validators=[Optional(), Length(max=128)])
    description = TextAreaField('Description', validators=[Optional()])
    submit = SubmitField('Save Tower')

class DrawerForm(FlaskForm):
    name = StringField('Drawer Name/Number (e.g., Drawer 1, Shelf A)', validators=[DataRequired(), Length(max=64)])
    # We'll populate choices for tower_id dynamically in the route
    tower_id = SelectField('Belongs to Tower', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save Drawer')

class BoxForm(FlaskForm):
    name = StringField('Box Name/Identifier (e.g., Box 001, P01 Cells)', validators=[DataRequired(), Length(max=64)])
    # We'll populate choices for drawer_id dynamically in the route
    drawer_id = SelectField('Belongs to Drawer', coerce=int, validators=[DataRequired()])
    rows = IntegerField('Number of Rows (e.g., 9)', default=9, validators=[DataRequired()])
    columns = IntegerField('Number of Columns (e.g., 9)', default=9, validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    submit = SubmitField('Save Box')

class CryoVialForm(FlaskForm):
    batch_name = StringField('Batch Name', validators=[DataRequired(), Length(max=128)])
    quantity_to_add = IntegerField(
        'Number of Vials to Add',
        default=1,
        validators=[DataRequired(), NumberRange(min=1, max=99)],
        render_kw={'min': 1, 'max': 99}
    )

    cell_line_id = SelectField('Cell Line', coerce=int, validators=[DataRequired()])

    # REMOVE THE FOLLOWING FIELDS:
    # box_id = SelectField('Box (Tower - Drawer - Box)', coerce=coerce_int_or_none, validators=[Optional()])
    # row_in_box = IntegerField('Row in Box (for single vial)', validators=[Optional()])
    # col_in_box = IntegerField('Column in Box (for single vial)', validators=[Optional()])

    passage_number = StringField('Passage Number (of these vials)',
                                 validators=[DataRequired(), Length(max=64)])
    date_frozen = DateField('Date Frozen (YYYY-MM-DD)', format='%Y-%m-%d',
                            validators=[DataRequired()])

    volume_ml = FloatField('Volume per Vial (uL)', validators=[Optional()])
    fluorescence_tag = StringField('Fluorescence Tag', validators=[Optional(), Length(max=128)])
    resistance = MultiCheckboxField(
        'Resistance',
        choices=[('Puro', 'Puro'), ('Blast', 'Blast'), ('Neo/G418', 'Neo/G418'), ('Zeo', 'Zeo')],
        validators=[Optional()]
    )
    parental_cell_line = StringField('Parental cell line', validators=[Optional(), Length(max=128)])
    concentration = StringField('Cell Concentration (e.g., 1x10^6 cells/mL)',
                                validators=[Optional(), Length(max=128)])

    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Next: Plan Placement') # Changed button text slightly

    # Simplified custom validate method
    def validate(self, extra_validators=None):
        if not super(CryoVialForm, self).validate(extra_validators):
            return False

        if self.quantity_to_add.data is not None and not (1 <= self.quantity_to_add.data <= 99):
            self.quantity_to_add.errors.append("Number of vials must be between 1 and 99.")
            return False
        return True

class VialUsageForm(FlaskForm):
    # This form might not even need fields if action is simple
    # Or it could have a field for "number of vials used" if one record represents multiple.
    # For now, a simple submit to mark as "Used" or "Depleted".
    new_status = SelectField('Mark as:', choices=[('Used', 'Used'), ('Depleted', 'Depleted'), ('Discarded', 'Discarded')], validators=[DataRequired()])
    notes = TextAreaField('Usage Notes (Optional)', validators=[Optional()])
    submit = SubmitField('Update Status')


class ManualVialForm(FlaskForm):
    """Form for admins to add a single vial at a specified position."""
    batch_id = IntegerField('Existing Batch ID', validators=[Optional()])
    batch_name = StringField('Batch Name', validators=[Optional(), Length(max=128)])
    cell_line_id = SelectField('Cell Line', coerce=int, validators=[DataRequired()])
    passage_number = StringField('Passage Number (of this vial)', validators=[DataRequired(), Length(max=64)])
    date_frozen = DateField('Date Frozen (YYYY-MM-DD)', format='%Y-%m-%d', validators=[DataRequired()])
    volume_ml = FloatField('Volume per Vial (uL)', validators=[Optional()])
    fluorescence_tag = StringField('Fluorescence Tag', validators=[Optional(), Length(max=128)])
    resistance = MultiCheckboxField(
        'Resistance',
        choices=[('Puro', 'Puro'), ('Blast', 'Blast'), ('Neo/G418', 'Neo/G418'), ('Zeo', 'Zeo')],
        validators=[Optional()],
    )
    parental_cell_line = StringField('Parental cell line', validators=[Optional(), Length(max=128)])
    concentration = StringField('Cell Concentration (e.g., 1x10^6 cells/mL)', validators=[Optional(), Length(max=128)])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Add Vial')

    def validate(self, extra_validators=None):
        if not super(ManualVialForm, self).validate(extra_validators):
            return False
        if not self.batch_id.data and not self.batch_name.data:
            self.batch_name.errors.append('Provide an existing batch ID or a new batch name.')
            return False
        return True




class CryoVialEditForm(FlaskForm):
    unique_vial_id_tag = StringField('Vial Tag', validators=[DataRequired(), Length(max=128)])
    cell_line_id = SelectField('Cell Line', coerce=int, validators=[DataRequired()])
    box_id = SelectField('Box (Tower - Drawer - Box)', coerce=int, validators=[DataRequired()])
    row_in_box = IntegerField('Row', validators=[DataRequired()])
    col_in_box = IntegerField('Column', validators=[DataRequired()])
    passage_number = StringField('Passage Number', validators=[Optional(), Length(max=64)])
    date_frozen = DateField('Date Frozen (YYYY-MM-DD)', format='%Y-%m-%d', validators=[DataRequired()])
    number_of_vials_at_creation = IntegerField('Number of Vials at Creation', validators=[Optional()])
    volume_ml = FloatField('Volume per Vial (uL)', validators=[Optional()])
    concentration = StringField('Cell Concentration (e.g., 1x10^6 cells/mL)', validators=[Optional(), Length(max=128)])
    fluorescence_tag = StringField('Fluorescence Tag', validators=[Optional(), Length(max=128)])
    resistance = MultiCheckboxField(
        'Resistance',
        choices=[('Puro', 'Puro'), ('Blast', 'Blast'), ('Neo/G418', 'Neo/G418'), ('Zeo', 'Zeo')],
        validators=[Optional()],
    )
    parental_cell_line = StringField('Parental cell line', validators=[Optional(), Length(max=128)])
    status = SelectField('Status', choices=[('Available','Available'),('Used','Used'),('Depleted','Depleted'),('Discarded','Discarded')], validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save Changes')


class ConfirmForm(FlaskForm):
    """Simple form asking user to type a confirmation phrase."""
    confirm = StringField('Type "confirm_hayer" to continue', validators=[DataRequired()])
    submit = SubmitField('Confirm')


class RestoreForm(FlaskForm):
    """Upload form for restoring a database backup."""
    backup_file = FileField('Backup File', validators=[DataRequired()])
    submit = SubmitField('Restore')


class BatchEditVialsForm(FlaskForm):
    """Form for admins to update multiple cryovials at once."""
    vial_tags = TextAreaField(
        'Vial Tags (comma or newline separated)', validators=[DataRequired()]
    )
    new_status = SelectField(
        'New Status',
        choices=[
            ('', 'No Change'),
            ('Available', 'Available'),
            ('Used', 'Used'),
            ('Depleted', 'Depleted'),
            ('Discarded', 'Discarded'),
        ],
        validators=[Optional()],
    )
    notes = TextAreaField('Append Notes', validators=[Optional()])
    submit = SubmitField('Apply Changes')


class EditBatchForm(FlaskForm):
    """Edit properties shared by all vials in a batch."""
    batch_name = StringField('Batch Name', validators=[DataRequired(), Length(max=128)])
    cell_line_id = SelectField('Cell Line', coerce=int, validators=[DataRequired()])
    passage_number = StringField('Passage Number', validators=[DataRequired(), Length(max=64)])
    date_frozen = DateField('Date Frozen (YYYY-MM-DD)', format='%Y-%m-%d', validators=[DataRequired()])
    volume_ml = FloatField('Volume per Vial (uL)', validators=[Optional()])
    concentration = StringField('Cell Concentration (e.g., 1x10^6 cells/mL)', validators=[Optional(), Length(max=128)])
    fluorescence_tag = StringField('Fluorescence Tag', validators=[Optional(), Length(max=128)])
    resistance = MultiCheckboxField(
        'Resistance',
        choices=[('Puro', 'Puro'), ('Blast', 'Blast'), ('Neo/G418', 'Neo/G418'), ('Zeo', 'Zeo')],
        validators=[Optional()],
    )
    parental_cell_line = StringField('Parental cell line', validators=[Optional(), Length(max=128)])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save Changes')

