from rest_framework import serializers


class AdvancePaymentSerializer(serializers.Serializer):
    description = serializers.CharField(required=False, allow_blank=True, max_length=255)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    rate = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=0, max_value=100)


class UnifiedTaxRequestSerializer(serializers.Serializer):
    REPORT_KIND_CHOICES = [
        ('initial', 'Первоначальный'),
        ('amended', 'Уточненный'),
        ('liquidation', 'Ликвидационный'),
    ]

    ACTIVITY_LINE_CHOICES = [
        ('trade_preferential', 'Торговая деятельность - льготная строка 050'),
        ('trade_general', 'Торговая деятельность - строки 053/056'),
        ('production', 'Производство/переработка/ПО/туризм - строки 060/063'),
        ('other', 'Прочие виды деятельности - строки 067/070'),
        ('public_catering', 'Общественное питание - строки 074/077'),
        ('garment_textile', 'Швейное и/или текстильное производство - строка 130'),
        ('jewelry', 'Ювелирные изделия - строка 133'),
        ('lottery', 'Лотерейная деятельность - строка 136'),
        ('sauna', 'Сауна - строка 139'),
        ('billiard', 'Бильярд - строка 142'),
        ('banya', 'Баня - строка 145'),
        ('creative_park', 'Резидент парка креативной индустрии - строка 148'),
        ('article_324_export', 'Режим статьи 324 НК КР - строка 151'),
        ('agri_procurement', 'Сельхоззаготовитель - строка 154'),
        ('milk_procurement', 'Сельхоззаготовитель молока - строка 157'),
        ('anonymous_subject_423', 'Обезличенный субъект по ст. 423 - строка 160'),
        ('fez_partial', 'СЭЗ с частичной переработкой - строка 163'),
        ('fez_unchanged', 'СЭЗ в неизмененном виде - строка 166'),
        ('school_catering_ip', 'Питание учащихся школ КР - строка 170'),
        ('state_real_estate_exchange', 'Обмен/передача недвижимости для госнужд - строка 173'),
        ('virtual_asset', 'Реализация виртуального актива - строка 176'),
        ('outside_kr', 'Деятельность вне территории КР - строка 179'),
    ]

    year = serializers.IntegerField(required=True, min_value=2000, max_value=2100)
    quarter = serializers.ChoiceField(choices=[1, 2, 3, 4], required=True)
    report_kind = serializers.ChoiceField(choices=REPORT_KIND_CHOICES, required=False, default='initial')

    tin = serializers.CharField(required=False, allow_blank=True, max_length=30)
    taxpayer_name = serializers.CharField(required=False, allow_blank=True, max_length=255)
    tax_office = serializers.CharField(required=False, allow_blank=True, max_length=255)
    contact_phone = serializers.CharField(required=False, allow_blank=True, max_length=50)

    activity_line_map = serializers.DictField(
        required=False,
        child=serializers.ChoiceField(choices=ACTIVITY_LINE_CHOICES),
        help_text='Ключ словаря - activity id или activity code, значение - строка формы STI-091.',
    )
    current_period_advance_payments = AdvancePaymentSerializer(many=True, required=False, default=list)
    previous_period_advance_offsets = AdvancePaymentSerializer(many=True, required=False, default=list)
    generate_pdf = serializers.BooleanField(required=False, default=True)


class UnifiedTaxReportResponseSerializer(serializers.Serializer):
    pdf_file = serializers.URLField(allow_null=True)
    verbal_report = serializers.CharField()
    ai_validation = serializers.CharField()
    ai_validation_status = serializers.ChoiceField(choices=['ok', 'unavailable'])
    validation_summary = serializers.CharField()
