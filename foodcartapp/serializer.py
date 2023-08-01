from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from phonenumber_field.validators import validate_international_phonenumber
from rest_framework import serializers

from .models import Order, OrderItem


class OrderProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ('product', 'quantity')


class OrderSerializer(serializers.ModelSerializer):
    products = OrderProductSerializer(many=True, allow_empty=False, write_only=True)
    phonenumber = serializers.CharField(validators=[RegexValidator(r'^\+\d{11}$')])

    class Meta:
        model = Order
        fields = ('products', 'phonenumber', 'firstname', 'lastname', 'address')

    def validate_phonenumber(self, phonenumber):
        if not phonenumber:
            raise serializers.ValidationError('Это поле обязательно')
        try:
            validate_international_phonenumber(phonenumber)
        except ValidationError:
            raise serializers.ValidationError('Введен некорректный номер телефона.')
        return phonenumber

# print(repr(OrderSerializer()))
