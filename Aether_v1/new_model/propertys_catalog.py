from config import MONTH_PATTERNS_SPA, NUMERIC_MONTH_PATTERNS

inverted_numeric_month_patterns = {v:k for k,v in NUMERIC_MONTH_PATTERNS.items()}

AMEX_CREDIT_PROPERTYS = {
    # Phrase properties
    'start_phrase' : [],
    'end_phrase' : [],
    
    # Column distribution properties
    'columns': [],
    'columns_row' : [],
    'date_column' : '',
    'description_column' : '',
    'amount_column' : [],
    'income_column' : '',
    'expense_column' : '',
    
    # Date properties
    'date_pattern' : r"",
    'date_groups' : (), # groups: (year, month, day)
    'month_pattern' : inverted_numeric_month_patterns,
    
    # Period properties
    'period_phrase' : [],
    'period_pattern' : r"",
    'year_group' : None,
    
}

BANORTE_DEBIT_PROPERTYS = {
    # Phrase properties
    'start_phrase' : ['detalle', 'de', 'movimientos', '(pesos)▼'],
    'end_phrase' : ['inversión', 'enlace', 'personal'],
    
    # Column distribution properties
    'columns': ['FECHA', 'DESCRIPCIÓN / ESTABLECIMIENTO', 'MONTO DEL DEPOSITO', 'MONTO DEL RETIRO', 'SALDO'],
    'columns_row' : ['FECHA', 'DESCRIPCIÓN / ESTABLECIMIENTO', 'MONTO DEL DEPOSITO', 'MONTO DEL RETIRO', 'SALDO'],
    'date_column' : 'FECHA',
    'description_column' : 'DESCRIPCIÓN / ESTABLECIMIENTO',
    'amount_column' : ['MONTO DEL DEPOSITO', 'MONTO DEL RETIRO'],
    'income_column' : 'MONTO DEL DEPOSITO',
    'expense_column' : 'MONTO DEL RETIRO',
    
    # Date properties
    'date_pattern' : r"(\d{2})-(\w{3})-(\d{2})",
    'date_groups' : (3, 2, 1), # groups: (year, month, day)
    'month_pattern' : inverted_numeric_month_patterns,
    
    # Period properties
    'period_phrase' : ['periodo'],
    'period_pattern' : r"(\d{2})/(Enero|Febrero|Marzo|Abril|Mayo|Junio|Julio|Agosto|Septiembre|Octubre|Noviembre|Diciembre)/(\d{4})",
    'year_group' : 3,
}

BANORTE_CREDIT_PROPERTYS = {
    
}

BBVA_DEBIT_PROPERTYS = {
    # Phrase properties
    'start_phrase' : ["detalle", "de", "movimientos", "realizados"],
    'end_phrase' : ["le", "informamos", "que", "puede"],
    
    # Column distribution properties
    'columns': ['OPER', 'LIQ', 'DESCRIPCION', 'REFERENCIA', 'CARGOS', 'ABONOS', 'OPERACION', 'LIQUIDACION'],
    'columns_row' : ['OPER', 'LIQ', 'DESCRIPCION', 'REFERENCIA', 'CARGOS', 'ABONOS', 'OPERACION', 'LIQUIDACION'],
    'date_column' : 'OPER',
    'description_column' : 'DESCRIPCION',
    'amount_column' : ['CARGOS', 'ABONOS'],
    'income_column' : 'ABONOS',
    'expense_column' : 'CARGOS',
    
    # Date properties
    'date_pattern' : r"^(\d{2})/([A-Z]{3})\b",
    'date_groups': (None, 2, 1), # groups: (year, month, day)
    'month_pattern' : inverted_numeric_month_patterns,
    
    # Period properties
    'period_phrase' : ['periodo'],
    'period_pattern' : r"(\d{2})/(\d{2})/(\d{4})",
    'year_group' : 3, 
}

BBVA_CREDIT_PROPERTYS = {
    # Phrase properties
    'start_phrase' : ['movimientos', 'efectuados'],
    'end_phrase' : ['resumen', 'informativo', 'de', 'beneficios'],
    
    # Column distribution properties
    'columns': ['FECHA AUTORIZACION', 'FECHA APLICACION', 'CONCEPTO', 'R.F.C.', 'REFERENCIA', 'IMPORTE CARGOS', 'IMPORTE ABONOS'],
    'columns_row' : ['AUTORIZACION', 'APLICACION', 'CARGOS', 'ABONOS'],
    'date_column' : 'FECHA AUTORIZACION',
    'description_column' : 'CONCEPTO',
    'amount_column' : ['IMPORTE CARGOS', 'IMPORTE ABONOS'],
    'income_column' : 'IMPORTE ABONOS',
    'expense_column' : 'IMPORTE CARGOS',
    
    # Date properties
    'date_pattern' : r"(\d{2})/(\d{2})/(\d{2})",
    'date_groups' : (3, 2, 1), # groups: (year, month, day)
    'month_pattern' : NUMERIC_MONTH_PATTERNS,
    
    # Period properties
    'period_phrase' : ['Periodo'],
    'period_pattern' : r"(\d{2})/(\d{2})/(\d{2})",
    'year_group' : 3,
}

BANAMEX_DEBIT_PROPERTYS = {
    
}

BANAMEX_CREDIT_PROPERTYS = {
    
}

HSBC_DEBIT_PROPERTYS = {
    
}

HSBC_CREDIT_PROPERTYS = {
    
}

INBURSA_DEBIT_PROPERTYS = {
    
}

INBURSA_CREDIT_PROPERTYS = {
    
}

NU_DEBIT_PROPERTYS = {
    
}

NU_CREDIT_PROPERTYS = {
    
}

SANTANDER_DEBIT_PROPERTYS = {
    
}

SANTANDER_CREDIT_PROPERTYS = {
    
}