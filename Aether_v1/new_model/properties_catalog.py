from config import MONTH_PATTERNS_SPA, NUMERIC_MONTH_PATTERNS

inverted_numeric_month_patterns = {v:k for k,v in NUMERIC_MONTH_PATTERNS.items()}

AMEX_CREDIT_PROPERTIES = {
    # Phrase properties
    'start_phrase' : [],
    'end_phrase' : [],
    
    # Column distribution properties
    'columns': [],
    'date_column' : '',
    'description_column' : '',
    'amount_column' : [],
    'income_column' : '',
    'expense_column' : '',
    'balance_column' : '',
    
    # Date properties
    'date_pattern' : r"",
    'date_groups' : (), # groups: (year, month, day)
    'month_pattern' : inverted_numeric_month_patterns,
    
    # Amount properties
    'income_sign': '',
    'expense_sign': '',
    
    # Period properties
    'period_phrase' : [],
    'period_pattern' : r"",
    'year_group' : None,
    
    # Trheshold properties
    'row_treshold_adjust' : False,
    'date_treshold_adjust' : False,
    'amount_treshold_adjust' : False,
}

BANORTE_DEBIT_PROPERTIES = {
    # Phrase properties
    'start_phrase' : ['detalle', 'de', 'movimientos', '(pesos)▼'],
    'end_phrase' : ['inversión', 'enlace', 'personal'],
    
    # Column distribution properties
    'columns': ['FECHA', 'DESCRIPCIÓN / ESTABLECIMIENTO', 'MONTO DEL DEPOSITO', 'MONTO DEL RETIRO', 'SALDO'],
    'date_column' : 'FECHA',
    'description_column' : 'DESCRIPCIÓN / ESTABLECIMIENTO',
    'amount_column' : ['MONTO DEL DEPOSITO', 'MONTO DEL RETIRO', 'SALDO'],
    'income_column' : 'MONTO DEL DEPOSITO',
    'expense_column' : 'MONTO DEL RETIRO',
    'balance_column' : 'SALDO',
    
    # Date properties
    'date_pattern' : r"(\d{2})-(\w{3})-(\d{2})",
    'date_groups' : (3, 2, 1), # groups: (year, month, day)
    'month_pattern' : inverted_numeric_month_patterns,
    
    # Amount properties
    'income_sign': None,
    'expense_sign': None,
    
    # Period properties
    'period_phrase' : ['periodo'],
    'period_pattern' : r"(\d{2})/(Enero|Febrero|Marzo|Abril|Mayo|Junio|Julio|Agosto|Septiembre|Octubre|Noviembre|Diciembre)/(\d{4})",
    'year_group' : 3,
    
    # Trheshold properties
    'row_treshold_adjust' : True,
    'date_treshold_adjust' : False,
    'amount_treshold_adjust' : False,
}

BANORTE_CREDIT_PROPERTIES = {
    # Phrase properties
    'start_phrase' : ['detalle', 'de', 'movimientos', 'del' ,'titular',  'en', 'm.n.'],
    'end_phrase' : ['si', 'solo', 'realizas', 'el', 'pago', 'mínimo'],
    
    # Column distribution properties
    'columns': ['Fecha', 'Concepto', 'RFC/CURP', 'Tipo de transacción', 'Importe'],
    'date_column' : 'Fecha',
    'description_column' : 'Concepto',
    'amount_column' : ['Importe'],
    'income_column' : 'Importe',
    'expense_column' : 'Importe',
    'balance_column' : None,
    
    # Date properties
    'date_pattern' : r"(\d{2})/(\d{2})",
    'date_groups' : (None, 2, 1), # groups: (year, month, day)
    'month_pattern' : inverted_numeric_month_patterns,
    
    # Amount properties
    'income_sign': '-',
    'expense_sign': None,
    
    # Period properties
    'period_phrase' : ['periodo'],
    'period_pattern' : None,
    'year_group' : None,
    
    # Trheshold properties
    'row_treshold_adjust' : False,
    'date_treshold_adjust' : False,
    'amount_treshold_adjust' : False,
}

BANORTE_NEW_CREDIT_FORMAT_PROPERTIES = {
    # Phrase properties
    'start_phrase' : ['cargos,', 'abonos', 'y', 'compras', 'regulares'],
    'end_phrase' : ['total', 'cargos'],
    
    # Column distribution properties
    'columns': ['Fecha de la operación', 'Fecha de cargo', 'Descripción del movimiento', 'Monto'],
    'date_column' : 'Fecha de la operación',
    'description_column' : 'Descripción del movimiento',
    'amount_column' : ['Monto'],
    'income_column' : None,
    'expense_column' : None,
    'balance_column' : None,
    
    # Date properties
    'date_pattern' : r"(\d{2})-(ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC)-(20\d{2})",
    'date_groups' : (3, 2, 1), # groups: (year, month, day)
    'month_pattern' : inverted_numeric_month_patterns,
    
    # Amount properties
    'income_sign': '-',
    'expense_sign': '+',
    
    # Period properties
    'period_phrase' : None,
    'period_pattern' : None,
    'year_group' : None,
    
    # Trheshold properties
    'row_treshold_adjust' : True,
    'date_treshold_adjust' : False,
    'amount_treshold_adjust' : True,
}

BBVA_DEBIT_PROPERTIES = {
    # Phrase properties
    'start_phrase' : ["detalle", "de", "movimientos", "realizados"],
    'end_phrase' : ["le", "informamos", "que", "puede"],
    
    # Column distribution properties
    'columns': ['OPER', 'LIQ', 'DESCRIPCION', 'REFERENCIA', 'CARGOS', 'ABONOS', 'OPERACION', 'LIQUIDACION'],
    'date_column' : 'OPER',
    'description_column' : 'DESCRIPCION',
    'amount_column' : ['CARGOS', 'ABONOS', 'LIQUIDACION'],
    'income_column' : 'ABONOS',
    'expense_column' : 'CARGOS',
    'balance_column' : 'LIQUIDACION',
    
    # Date properties
    'date_pattern' : r"^(\d{2})/([A-Z]{3})\b",
    'date_groups': (None, 2, 1), # groups: (year, month, day)
    'month_pattern' : inverted_numeric_month_patterns,
    
    # Amount properties
    'income_sign': None,
    'expense_sign': None,
    
    # Period properties
    'period_phrase' : ['periodo'],
    'period_pattern' : r"(\d{2})/(\d{2})/(\d{4})",
    'year_group' : 3, 
    
    # Trheshold properties
    'row_treshold_adjust' : False,
    'date_treshold_adjust' : False,
    'amount_treshold_adjust' : False,
}

BBVA_CREDIT_PROPERTIES = {
    # Phrase properties
    'start_phrase' : ['movimientos', 'efectuados'],
    'end_phrase' : ['resumen', 'informativo', 'de', 'beneficios'],
    
    # Column distribution properties
    'columns': ['FECHA AUTORIZACION', 'FECHA APLICACION', 'CONCEPTO', 'R.F.C.', 'REFERENCIA', 'IMPORTE CARGOS', 'IMPORTE ABONOS'],
    'date_column' : 'FECHA AUTORIZACION',
    'description_column' : 'CONCEPTO',
    'amount_column' : ['IMPORTE CARGOS', 'IMPORTE ABONOS'],
    'income_column' : 'IMPORTE ABONOS',
    'expense_column' : 'IMPORTE CARGOS',
    'balance_column' : None,
    
    # Date properties
    'date_pattern' : r"(\d{2})/(\d{2})/(\d{2})",
    'date_groups' : (3, 2, 1), # groups: (year, month, day)
    'month_pattern' : NUMERIC_MONTH_PATTERNS,
    
    # Amount properties
    'income_sign': None,
    'expense_sign': None,
    
    # Period properties
    'period_phrase' : None,
    'period_pattern' : None,
    'year_group' : None,
    
    # Trheshold properties
    'row_treshold_adjust' : True,
    'date_treshold_adjust' : False,
    'amount_treshold_adjust' : False,
}

BBVA_NEW_CREDIT_FORMAT_PROPERTIES = {
    # Phrase properties
    'start_phrase' : ['cargos,compras', 'y', 'abonos'],
    'end_phrase' : ['total', 'cargos'],
    
    # Column distribution properties
    'columns': ['Fecha de la operación', 'Fecha de cargo', 'Descripción del movimiento', 'Monto'],
    'date_column' : 'Fecha de la operación',
    'description_column' : 'Descripción del movimiento',
    'amount_column' : ['Monto'],
    'income_column' : None,
    'expense_column' : None,
    'balance_column' : None,
    
    # Date properties
    'date_pattern' : r"(\d{2})-(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)-(20\d{2})",
    'date_groups' : (3, 2, 1), # groups: (year, month, day)
    'month_pattern' : {month.lower() : num for num, month in NUMERIC_MONTH_PATTERNS.items()},
    
    # Amount properties
    'income_sign': '-',
    'expense_sign': '+',
    
    # Period properties
    'period_phrase' : None,
    'period_pattern' : None,
    'year_group' : None,
    
    # Trheshold properties
    'row_treshold_adjust' : True,
    'date_treshold_adjust' : False,
    'amount_treshold_adjust' : True,
}

BANAMEX_DEBIT_PROPERTIES = {
    
}

BANAMEX_CREDIT_PROPERTIES = {
    # Phrase properties
    'start_phrase' : ['detalle', 'de', 'operaciones'],
    'end_phrase' : ['mensualidad*', 'aplica', 'para', 'compras', 'a', 'plazos.'],
    
    # Column distribution properties
    'columns': ['Fecha', 'Concepto/Giro de Negocio Mensualidad * / Tipos de Cambio', 'Población / RFC Moneda Ext.', 'Otras Divisas', 'Pesos'],
    'date_column' : 'Fecha',
    'description_column' : 'Concepto/Giro de Negocio Mensualidad * / Tipos de Cambio',
    'amount_column' : ['Pesos'],
    'income_column' : 'Pesos',
    'expense_column' : 'Pesos',
    'balance_column' : None,
    
    # Date properties
    'date_pattern' : r"(Ene|Feb|Mar|Abr|May|Jun|Jul|Ago|Sep|Oct|Nov|Dic) (\d{2})",
    'date_groups' : (None, 1, 2), # groups: (year, month, day)
    'month_pattern' : {month.capitalize(): num for num, month in NUMERIC_MONTH_PATTERNS.items()},
    
    # Amount properties
    'income_sign': '-',
    'expense_sign': None,
    
    # Period properties
    'period_phrase' : ['fecha', 'de', 'corte'],
    'period_pattern' : None,
    'year_group' : None,
    
    # Trheshold properties
    'row_treshold_adjust' : True,
    'date_treshold_adjust' : False,
    'amount_treshold_adjust' : True,
}

BANAMEX_NEW_CREDIT_FORMAT_PROPERTIES = {
    # Phrase properties
    'start_phrase' : ['cargos,', 'abonos', 'y', 'compras', 'regulares'],
    'end_phrase' : ['total', 'cargos'],
    
    # Column distribution properties
    'columns': ['Fecha de la operación', 'Fecha de cargo', 'Descripción del movimiento', 'Monto'],
    'date_column' : 'Fecha de la operación',
    'description_column' : 'Descripción del movimiento',
    'amount_column' : ['Monto'],
    'income_column' : None,
    'expense_column' : None,
    'balance_column' : None,
    
    # Date properties
    'date_pattern' : r"(\d{2})-(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)-(20\d{2})",
    'date_groups' : (3, 2, 1), # groups: (year, month, day)
    'month_pattern' : {month.lower() : num for num, month in NUMERIC_MONTH_PATTERNS.items()},
    
    # Amount properties
    'income_sign': '-',
    'expense_sign': '+',
    
    # Period properties
    'period_phrase' : None,
    'period_pattern' : None,
    'year_group' : None,
    
    # Trheshold properties
    'row_treshold_adjust' : False,
    'date_treshold_adjust' : False,
    'amount_treshold_adjust' : True,
}

HSBC_DEBIT_PROPERTIES = {
    
}

HSBC_CREDIT_PROPERTIES = {
    # Phrase properties
    'start_phrase' : ['detalle', 'de', 'movimientos'],
    'end_phrase' : ['información', "spei´s", 'recibidos'],
    
    # Column distribution properties
    'columns': ['Fecha', 'Concepto', 'Importe'],
    'date_column' : 'Fecha',
    'description_column' : 'Concepto',
    'amount_column' : ['Importe'],
    'income_column' : 'Importe',
    'expense_column' : 'Importe',
    'balance_column' : None,
    
    # Date properties
    'date_pattern' : r"(\d{2}) (ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC)",
    'date_groups' : (None, 2, 1), # groups: (year, month, day)
    'month_pattern' : inverted_numeric_month_patterns,
    
    # Amount properties
    'income_sign': '-',
    'expense_sign': None,
    
    # Period properties
    'period_phrase' : ['fecha', 'de', 'corte'],
    'period_pattern' : None,
    'year_group' : None,
    
    # Trheshold properties
    'row_treshold_adjust' : True,
    'date_treshold_adjust' : False,
    'amount_treshold_adjust' : False,
}

INBURSA_DEBIT_PROPERTIES = {
    # Phrase properties
    'start_phrase' : ['detalle', 'de', 'movimientos'],
    'end_phrase' : ['movimientos', 'por', 'aclaracion'],
    
    # Column distribution properties
    'columns': ['FECHA', 'REFERENCIA', 'CONCEPTO', 'CARGOS', 'ABONOS', 'SALDO'],
    'date_column' : 'FECHA',
    'description_column' : 'CONCEPTO',
    'amount_column' : ['CARGOS', 'ABONOS', 'SALDO'],
    'income_column' : 'ABONOS',
    'expense_column' : 'CARGOS',
    'balance_column' : 'SALDO',
    
    # Date properties
    'date_pattern' : r"(ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC) (\d{2})",
    'date_groups' : (None, 1, 2), # groups: (year, month, day)
    'month_pattern' : inverted_numeric_month_patterns,
    
    # Amount properties
    'income_sign': None,
    'expense_sign': None,
    
    # Period properties
    'period_phrase' : ['periodo'],
    'period_pattern' : None,
    'year_group' : None,
    
    # Trheshold properties
    'row_treshold_adjust' : True,
    'date_treshold_adjust' : False,
    'amount_treshold_adjust' : True,
}

INBURSA_CREDIT_PROPERTIES = {
    # Phrase properties
    'start_phrase' : ['movimientos', 'del', 'periodo'],
    'end_phrase' : ['resumen', 'de', 'promociones', 'a', 'meses', 'sin', 'interes'],
    
    # Column distribution properties
    'columns': ['Fecha', 'Descripción', 'Cantidad (pesos)'],
    'date_column' : 'Fecha',
    'description_column' : 'Descripción',
    'amount_column' : ['Cantidad (pesos)'],
    'income_column' : 'Cantidad (pesos)',
    'expense_column' : 'Cantidad (pesos)',
    'balance_column' : None,
    
    # Date properties
    'date_pattern' : r"(\d{2})/(\d{2})",
    'date_groups' : (None, 1, 2), # groups: (year, month, day)
    'month_pattern' : NUMERIC_MONTH_PATTERNS,
    
    # Amount properties
    'income_sign': '-',
    'expense_sign': None,
    
    # Period properties
    'period_phrase' : ['resumen', 'del', 'periodo'],
    'period_pattern' : None,
    'year_group' : None,
    
    # Trheshold properties
    'row_treshold_adjust' : True,
    'date_treshold_adjust' : False,
    'amount_treshold_adjust' : True,
}

NU_DEBIT_PROPERTIES = {
    # Phrase properties
    'start_phrase' : ['detalle', 'de', 'movimientos', 'en', 'tu', 'cuenta'],
    'end_phrase' : ['con', 'estos', 'movimientos,'],
    
    # Column distribution properties
    'columns': [
        'FECHA',
        r'(DE) (\d{2}) (ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC) (A) (\d{2}) (ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC) (\(\d{2}) (DÍAS\))',
        'MONTO EN PESOS MEXICANOS'
    ],
    'date_column' : 'FECHA',
    'description_column' : r'(DE) (\d{2}) (ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC) (A) (\d{2}) (ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC) (\(\d{2}) (DÍAS\))',
    'amount_column' : ['MONTO EN PESOS MEXICANOS'],
    'income_column' : 'MONTO EN PESOS MEXICANOS',
    'expense_column' : 'MONTO EN PESOS MEXICANOS',
    'balance_column' : None,
    
    # Date properties
    'date_pattern' : r"(\d{2}) (ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC) (20\d{2})",
    'date_groups' : (3, 2, 1), # groups: (year, month, day)
    'month_pattern' : inverted_numeric_month_patterns,
    
    # Amount properties
    'income_sign': '+',
    'expense_sign': '-',
    
    # Period properties
    'period_phrase' : None,
    'period_pattern' : None,
    'year_group' : None,
    
    # Trheshold properties
    'row_treshold_adjust' : False,
    'date_treshold_adjust' : True,
    'amount_treshold_adjust' : False,
}

NU_CREDIT_PROPERTIES = {
    # Phrase properties
    'start_phrase' : ['transacciones'],
    'end_phrase' : ['saldo', 'final', 'del', 'periodo'],
    
    # Column distribution properties
    'columns': [
        'TRANSACCIONES',
        r'(DE) (\d{2}) (ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC) (A) (\d{2}) (ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC) (\(\d{2}) (DÍAS\))',
        'MONTOS EN PESOS MEXICANOS'
    ],
    'date_column' : 'TRANSACCIONES',
    'description_column' : r'(DE) (\d{2}) (ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC) (A) (\d{2}) (ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC) (\(\d{2}) (DÍAS\))',
    'amount_column' : ['MONTOS EN PESOS MEXICANOS'],
    'income_column' : 'MONTOS EN PESOS MEXICANOS',
    'expense_column' : 'MONTOS EN PESOS MEXICANOS',
    'balance_column' : None,
    
    # Date properties
    'date_pattern' : r"(\d{2}) (ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC)",
    'date_groups' : (None, 2, 1), # groups: (year, month, day)
    'month_pattern' : inverted_numeric_month_patterns,
    
    # Amount properties
    'income_sign': '-',
    'expense_sign': None,
    
    # Period properties
    'period_phrase' : ['periodo'],
    'period_pattern' : None,
    'year_group' : None,
    
    # Trheshold properties
    'row_treshold_adjust' : False,  
    'date_treshold_adjust' : True,
    'amount_treshold_adjust' : False
}

SANTANDER_DEBIT_PROPERTIES = {
    
}

SANTANDER_CREDIT_PROPERTIES = {
    
}