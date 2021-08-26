from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget
from .models import Item, OrderItem, Order
from django.forms import ChoiceField
from django.forms.widgets import Select
import copy
from django.core.validators import RegexValidator

PAYMENT_CHOICES = (
    ('S', 'Stripe'),
    ('P', 'PayPal')
)

SIZE_CHOICES = (
    ('S', 'S'),
    ('M', 'M'),
    ('L', 'L'),
    ('XL', 'XL')
)

COLOR_CHOICES = (
    ('', ''),
    ('', '')
)

DEPARTMENT_CHOICES = (
    ('Beni', 'Beni'),
    ('Chuquisaca', 'Chuquisaca'),
    ('Cochabamba', 'Cochabamba'),
    ('La Paz', 'La Paz'),
    ('Oruro', 'Oruro'),
    ('Pando', 'Pando'),
    ('Potosí', 'Potosí'),
    ('Santa Cruz', 'Santa Cruz'),
    ('Tarija', 'Tarija')
)

# override class Choice Field to avoid validation
class MyChoiceField(ChoiceField):
    widget = Select
    default_error_messages = {
        'invalid_choice': ('Select a valid choice. %(value)s is not one of the available choices.'),
    }

    def __init__(self, *, choices=(), **kwargs):
        super().__init__(**kwargs)
        self.choices = choices

    def __deepcopy__(self, memo):
        result = super().__deepcopy__(memo)
        result._choices = copy.deepcopy(self._choices, memo)
        return result

    def _get_choices(self):
        return self._choices

    def _set_choices(self, value):
        # Setting choices also sets the choices on the widget.
        # choices can be any iterable, but we call list() on it because
        # it will be consumed more than once.
        if callable(value):
            value = CallableChoiceIterator(value)
        else:
            value = list(value)

        self._choices = self.widget.choices = value

    choices = property(_get_choices, _set_choices)

    def to_python(self, value):
        """Return a string."""
        if value in self.empty_values:
            return ''
        return str(value)

    def validate(self, value):
        """Validate that the input is in self.choices."""
        """super().validate(value)
        if value and not self.valid_value(value):
            raise ValidationError(
                self.error_messages['invalid_choice'],
                code='invalid_choice',
                params={'value': value},
            )"""

    def valid_value(self, value):
        """Check to see if the provided value is a valid choice."""
        text_value = str(value)
        for k, v in self.choices:
            if isinstance(v, (list, tuple)):
                # This is an optgroup, so look inside the group for options
                for k2, v2 in v:
                    if value == k2 or text_value == str(k2):
                        return True
            else:
                if value == k or text_value == str(k):
                    return True
        return False


class OrderItemForm(forms.Form):
    chosenColor = MyChoiceField(widget=forms.Select, choices=COLOR_CHOICES)
    chosenSize = forms.ChoiceField(widget=forms.RadioSelect(
        attrs={
            'class': "form-check-inline custom-radio-list m-0"
        }
    ), choices=SIZE_CHOICES)
    quantity = forms.IntegerField(widget=forms.NumberInput(
        attrs={
            'class': "form-control",
            'style': "width: 20%; text-align: center; disabled;",
            'type': "number",
            'min': "1",
            'value': "1"
        }
    ))


class CheckoutForm(forms.Form):
    chosen_department = forms.ChoiceField(widget=forms.Select, choices=DEPARTMENT_CHOICES)
    nombre = forms.CharField(widget=forms.TextInput(
        attrs={
            'class': 'form-control',
            'placeholder': 'nombre'
        }
    ))
    apellido = forms.CharField(widget=forms.TextInput(
        attrs={
            'class': 'form-control',
            'placeholder': 'apellido'
        }
    ))
    phoneNumber = forms.CharField(max_length=16,
                                  widget=forms.TextInput(
                                      attrs={
                                          'class': 'form-control',
                                          'placeholder': 'número',
                                          'value': '+591'
                                      }))

