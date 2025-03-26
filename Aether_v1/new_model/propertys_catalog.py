AMEX_CREDIT_PROPERTYS = {
    
}

BANORTE_DEBIT_PROPERTYS = {
    'start_phrase' : ['detalle', 'de', 'movimientos', '(pesos)▼'],
    'end_phrase' : ['inversión', 'enlace', 'personal'],
    'columns': ['FECHA', 'DESCRIPCIÓN / ESTABLECIMIENTO', 'MONTO DEL DEPOSITO', 'MONTO DEL RETIRO', 'SALDO'],
    'date_column' : 'FECHA',
    'description_column' : 'DESCRIPCIÓN',
    'date_pattern' : r"(\d{2})-(\w{3})-(\d{2})"
}

BANORTE_CREDIT_PROPERTYS = {
    
}

BBVA_DEBIT_PROPERTYS = {
    'start_phrase' : ["detalle", "de", "movimientos", "realizados"],
    'end_phrase' : ["le", "informamos", "que", "puede"],
    'columns': ['OPER', 'LIQ', 'DESCRIPCION', 'REFERENCIA', 'CARGOS', 'ABONOS', 'OPERACION', 'LIQUIDACION'],
    'date_column' : 'OPER',
    'description_column' : 'DESCRIPCION',
    'amount_column' : ['CARGOS', 'ABONOS'],
    'income_column' : 'ABONOS',
    'expense_column' : 'CARGOS',
    'date_pattern' : r"^(\d{2})/([A-Z]{3})\b",
    'period_phrase' : ['periodo'],
    'period_pattern' : r"(\d{2})/(\d{2})/(\d{4})",
    'year_group' : 3, 
}

BBVA_CREDIT_PROPERTYS = {
    'start_phrase' : ['movimientos', 'efectuados'],
    'end_phrase': ['resumen', 'informativo', 'de', 'beneficios'],
    'columns' : []
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