from config import MONTH_PATTERNS_SPA, NUMERIC_MONTH_PATTERNS

inverted_numeric_month_patterns = {v:k for k,v in NUMERIC_MONTH_PATTERNS.items()}

AMEX_CREDIT_PROPERTIES = {
    # Bank properties
    'bank' : 'amex',
    'statement_type' : 'credit',
    'new_format' : False,
    
    # Phrase properties
    'start_phrase' : [],
    'end_phrase' : [],
    
    # Column distribution properties
    'columns': [],
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
}

BANORTE_DEBIT_PROPERTIES = {
    # Bank properties
    'bank' : 'banorte',
    'statement_type' : 'debit',
    'new_format' : None,
    
    # Phrase properties
    'start_phrase' : ['detalle', 'de', 'movimientos', '(pesos)▼'],
    'end_phrase' : ['inversión', 'enlace', 'personal'],
    'initial_balance_phrase' : ['saldo', 'inicial', 'del', 'periodo'],
    'initial_balance_description' : 'SALDO ANTERIOR',
    
    # Column distribution properties
    'columns': ['FECHA', 'DESCRIPCIÓN / ESTABLECIMIENTO', 'MONTO DEL DEPOSITO', 'MONTO DEL RETIRO', 'SALDO'],
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
    
}

BANORTE_CREDIT_PROPERTIES = {   
    # Bank properties
    'bank' : 'banorte',
    'statement_type' : 'credit',
    'new_format' : False,
    
    # Phrase properties
    'start_phrase' : ['detalle', 'de', 'movimientos', 'del' ,'titular',  'en', 'm.n.'],
    'end_phrase' : ['si', 'solo', 'realizas', 'el', 'pago', 'mínimo'],
    
    # Column distribution properties
    'columns': ['Fecha', 'Concepto', 'RFC/CURP', 'Tipo de transacción', 'Importe'],
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
    
}

BANORTE_NEW_CREDIT_FORMAT_PROPERTIES = {
    # Bank properties
    'bank' : 'banorte',
    'statement_type' : 'credit',
    'new_format' : True,
    
    # Phrase properties
    'start_phrase' : ['cargos,', 'abonos', 'y', 'compras', 'regulares'],
    'end_phrase' : ['total', 'cargos'],
    
    # Column distribution properties
    'columns': ['Fecha de la operación', 'Fecha de cargo', 'Descripción del movimiento', 'Monto'],
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
    
}

BBVA_DEBIT_PROPERTIES = {
    # Bank properties
    'bank' : 'bbva',
    'statement_type' : 'debit',
    'new_format' : None,
    
    # Phrase properties
    'start_phrase' : ["detalle", "de", "movimientos", "realizados"],
    'end_phrase' : ["le", "informamos", "que", "puede"],
    'initial_balance_phrase' : ['saldo', 'anterior'],
    'initial_balance_description' : None,
    
    # Column distribution properties
    'columns': ['OPER', 'LIQ', 'DESCRIPCION', 'REFERENCIA', 'CARGOS', 'ABONOS', 'OPERACION', 'LIQUIDACION'],
    'amount_column' : ['CARGOS', 'ABONOS', 'OPERACION', 'LIQUIDACION'],
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
    
}

BBVA_CREDIT_PROPERTIES = {
    # Bank properties
    'bank' : 'bbva',
    'statement_type' : 'credit',
    'new_format' : False,
    
    # Phrase properties
    'start_phrase' : ['movimientos', 'efectuados'],
    'end_phrase' : ['resumen', 'informativo', 'de', 'beneficios'],
    
    # Column distribution properties
    'columns': ['FECHA AUTORIZACION', 'FECHA APLICACION', 'CONCEPTO', 'R.F.C.', 'REFERENCIA', 'IMPORTE CARGOS', 'IMPORTE ABONOS'],
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
    
}

BBVA_NEW_CREDIT_FORMAT_PROPERTIES = {
    # Bank properties
    'bank' : 'bbva',
    'statement_type' : 'credit',
    'new_format' : True,
    
    # Phrase properties
    'start_phrase' : ['cargos,compras', 'y', 'abonos'],
    'end_phrase' : ['total', 'cargos'],
    
    # Column distribution properties
    'columns': ['Fecha de la operación', 'Fecha de cargo', 'Descripción del movimiento', 'Monto'],
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
    
}

BANAMEX_DEBIT_PROPERTIES = {
    
}

BANAMEX_CREDIT_PROPERTIES = {
    # Bank properties
    'bank' : 'banamex',
    'statement_type' : 'credit',
    'new_format' : False,
    
    # Phrase properties
    'start_phrase' : ['detalle', 'de', 'operaciones'],
    'end_phrase' : ['mensualidad*', 'aplica', 'para', 'compras', 'a', 'plazos.'],
    
    # Column distribution properties
    'columns': ['Fecha', 'Concepto/Giro de Negocio Mensualidad * / Tipos de Cambio', 'Población / RFC Moneda Ext.', 'Otras Divisas', 'Pesos'],
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
    
}

BANAMEX_NEW_CREDIT_FORMAT_PROPERTIES = {
    # Bank properties
    'bank' : 'banamex',
    'statement_type' : 'credit',
    'new_format' : True,
    
    # Phrase properties
    'start_phrase' : ['cargos,', 'abonos', 'y', 'compras', 'regulares'],
    'end_phrase' : ['total', 'cargos'],
    
    # Column distribution properties
    'columns': ['Fecha de la operación', 'Fecha de cargo', 'Descripción del movimiento', 'Monto'],
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
    
}

HSBC_DEBIT_PROPERTIES = {
    
}

HSBC_CREDIT_PROPERTIES = {
    # Bank properties
    'bank' : 'hsbc',
    'statement_type' : 'credit',
    'new_format' : False,
    
    # Phrase properties
    'start_phrase' : ['detalle', 'de', 'movimientos'],
    'end_phrase' : ['información', "spei´s", 'recibidos'],
    
    # Column distribution properties
    'columns': ['Fecha', 'Concepto', 'Importe'],    
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
    
}

INBURSA_DEBIT_PROPERTIES = {
    # Bank properties
    'bank' : 'inbursa',
    'statement_type' : 'debit',
    'new_format' : None,
    
    # Phrase properties
    'start_phrase' : ['detalle', 'de', 'movimientos'],
    'end_phrase' : ['movimientos', 'por', 'aclaracion'],
    'initial_balance_phrase' : ['saldo', 'anterior'],
    'initial_balance_description' : 'BALANCE INICIAL',
    
    # Column distribution properties
    'columns': ['FECHA', 'REFERENCIA', 'CONCEPTO', 'CARGOS', 'ABONOS', 'SALDO'],
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
    
}

INBURSA_CREDIT_PROPERTIES = {
    # Bank properties
    'bank' : 'inbursa',
    'statement_type' : 'credit',
    'new_format' : False,
    
    # Phrase properties
    'start_phrase' : ['movimientos', 'del', 'periodo'],
    'end_phrase' : ['resumen', 'de', 'promociones', 'a', 'meses', 'sin', 'interes'],
    
    # Column distribution properties
    'columns': ['Fecha', 'Descripción', 'Cantidad (pesos)'],
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

}

NU_DEBIT_PROPERTIES = { 
    # Bank properties
    'bank' : 'nu',
    'statement_type' : 'debit',
    'new_format' : None,
    
    # Phrase properties
    'start_phrase' : ['detalle', 'de', 'movimientos', 'en', 'tu', 'cuenta'],
    'end_phrase' : ['con', 'estos', 'movimientos,'],
    'initial_balance_phrase' : ['saldo', 'inicial'],
    'initial_balance_description' : None,
    
    # Column distribution properties
    'columns': [
        'FECHA',
        r'(DE) (\d{2}) (ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC) (A) (\d{2}) (ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC) (\(\d{2}) (DÍAS\))',
        'MONTO EN PESOS MEXICANOS'
    ],
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
    
}

NU_CREDIT_PROPERTIES = {
    # Bank properties
    'bank' : 'nu',
    'statement_type' : 'credit',
    'new_format' : False,
    
    # Phrase properties
    'start_phrase' : ['transacciones'],
    'end_phrase' : ['saldo', 'final', 'del', 'periodo'],
    
    # Column distribution properties
    'columns': [
        'TRANSACCIONES',
        r'(DE) (\d{2}) (ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC) (A) (\d{2}) (ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC) (\(\d{2}) (DÍAS\))',
        'MONTOS EN PESOS MEXICANOS'
    ],
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
    
}

SANTANDER_DEBIT_PROPERTIES = {
    
}

SANTANDER_CREDIT_PROPERTIES = {
    
}