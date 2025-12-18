from models.amounts import AmountSignType, AmountColumns, AmountSigns
from models.bank_properties import BankProperties, BankName, StatementType
from models.dates import DateGroups
from constants.dates import MONTH_PATTERNS
from ..data_processing import NuSpecialDataFiltering

class BankPropertiesFactory:
    """
    Factory class for creating and managing bank properties.
    Uses lazy loading to register only the properties that are actually needed.
    """
    
    _registry: dict[tuple[BankName, StatementType, bool | None], BankProperties] = {}

    @classmethod
    def _register_banorte_debit(cls):
        """Register Banorte debit properties"""
        cls._registry[(BankName.BANORTE, StatementType.DEBIT, None)] = BankProperties(
            bank=BankName.BANORTE,
            statement_type=StatementType.DEBIT,
            new_format=None,
            start_phrase=['detalle', 'de', 'movimientos', '(pesos)▼'],
            end_phrase=['inversión', 'enlace', 'personal'],
            initial_balance_phrase=['saldo', 'inicial', 'del', 'periodo'],
            final_balance_phrase=['saldo', 'actual'],
            initial_balance_description='SALDO ANTERIOR',
            generated_amount_phrase=['intereses', 'netos', 'ganados'],
            period_phrase=['información', 'del', 'periodo'],
            columns=['FECHA', 'DESCRIPCIÓN / ESTABLECIMIENTO', 'MONTO DEL DEPOSITO', 'MONTO DEL RETIRO', 'SALDO'],
            amount_columns=AmountColumns(
                income='MONTO DEL DEPOSITO', 
                expense='MONTO DEL RETIRO', 
                balance='SALDO',
                all_list=['MONTO DEL DEPOSITO', 'MONTO DEL RETIRO', 'SALDO']
            ),
            date_pattern=r"(\d{2})-(\w{3})-(\d{2})",
            date_groups=DateGroups(year=3, month=2, day=1),
            month_pattern= MONTH_PATTERNS.abbr_to_num,
            amount_signs=AmountSigns(
                income=AmountSignType.NEUTRAL,
                expense=AmountSignType.NEUTRAL
            ),
            period_pattern=r"(\d{2})/(Enero|Febrero|Marzo|Abril|Mayo|Junio|Julio|Agosto|Septiembre|Octubre|Noviembre|Diciembre)/(\d{4})",
            period_month_pattern=MONTH_PATTERNS.month_to_num,
            period_group=DateGroups(year=3, month=2, day=1),            
        )

    @classmethod
    def _register_banorte_credit_old(cls):
        """Register Banorte credit old format properties"""
        cls._registry[(BankName.BANORTE, StatementType.CREDIT, False)] = BankProperties(
            bank=BankName.BANORTE,
            statement_type=StatementType.CREDIT,
            new_format=False,
            start_phrase=['detalle', 'de', 'movimientos', 'del' ,'titular',  'en', 'm.n.'],
            end_phrase=['si', 'solo', 'realizas', 'el', 'pago', 'mínimo'],
            period_phrase=['periodo'],
            columns=['Fecha', 'Concepto', 'RFC/CURP', 'Tipo de transacción', 'Importe'],
            amount_columns=AmountColumns(
                income='Importe',
                expense='Importe',
                balance=None,
                all_list=['Importe']
            ),
            date_pattern=r"(\d{2})/(\d{2})",
            date_groups=DateGroups(year=None, month=2, day=1),
            month_pattern=MONTH_PATTERNS.abbr_to_num,
            amount_signs=AmountSigns(
                income=AmountSignType.NEGATIVE,
                expense=AmountSignType.NEUTRAL
            ),
            period_pattern=r'(\d{1,2}) (Enero|Febrero|Marzo|Abril|Mayo|Junio|Julio|Agosto|Septiembre|Octubre|Noviembre|Diciembre),? (\d{4})',
            period_month_pattern=MONTH_PATTERNS.month_to_num,
            period_group=DateGroups(year=3, month=2, day=1)
        )

    @classmethod
    def _register_banorte_credit_new(cls):
        """Register Banorte credit new format properties"""
        cls._registry[(BankName.BANORTE, StatementType.CREDIT, True)] = BankProperties(
            bank=BankName.BANORTE,
            statement_type=StatementType.CREDIT,
            new_format=True,
            start_phrase=['cargos,', 'abonos', 'y', 'compras', 'regulares'],
            end_phrase=['total', 'cargos'],
            period_phrase= ['tu', 'pago', 'requerido', 'este', 'periodo'],
            columns=['Fecha de la operación', 'Fecha de cargo', 'Descripción del movimiento', 'Monto'],
            amount_columns=AmountColumns(
                income='Monto',
                expense='Monto',
                balance=None,
                all_list=['Monto']
            ),
            date_pattern=r"(\d{2})-(ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC)-(20\d{2})",
            date_groups=DateGroups(year=3, month=2, day=1),
            month_pattern=MONTH_PATTERNS.abbr_to_num,
            amount_signs=AmountSigns(
                income=AmountSignType.NEGATIVE,
                expense=AmountSignType.POSITIVE
            ),
            period_pattern=r"(\d{2})-(ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC)-(20\d{2})",
            period_month_pattern=MONTH_PATTERNS.abbr_to_num,
            period_group=DateGroups(year=3, month=2, day=1)
        )

    @classmethod
    def _register_bbva_debit(cls):
        """Register BBVA debit properties"""
        cls._registry[(BankName.BBVA, StatementType.DEBIT, None)] = BankProperties(
            bank=BankName.BBVA,
            statement_type=StatementType.DEBIT,
            new_format=None,
            start_phrase=["detalle", "de", "movimientos", "realizados"],
            end_phrase=["le", "informamos", "que", "puede"],
            initial_balance_phrase=['saldo', 'anterior'],
            final_balance_phrase=['saldo', 'final'],
            initial_balance_description=None,
            generated_amount_phrase=['Intereses', 'a', 'favor'],
            period_phrase=['periodo'],
            columns=['OPER', 'LIQ', 'DESCRIPCION', 'REFERENCIA', 'CARGOS', 'ABONOS', 'OPERACION', 'LIQUIDACION'],
            amount_columns=AmountColumns(
                income='ABONOS',
                expense='CARGOS',
                balance='LIQUIDACION',
                all_list=['CARGOS', 'ABONOS', 'OPERACION', 'LIQUIDACION']
            ),
            date_pattern=r"^(\d{2})/([A-Z]{3})\b",
            date_groups=DateGroups(month=2, day=1),
            month_pattern=MONTH_PATTERNS.abbr_to_num,
            amount_signs=AmountSigns(
                income=AmountSignType.NEUTRAL,
                expense=AmountSignType.NEUTRAL
            ),
            period_pattern=r"(\d{2})/(\d{2})/(\d{4})",
            period_month_pattern=None,
            period_group=DateGroups(year=3, month=2, day=1)
        )

    @classmethod
    def _register_bbva_credit_old(cls):
        """Register BBVA credit old format properties"""
        cls._registry[(BankName.BBVA, StatementType.CREDIT, False)] = BankProperties(
            bank=BankName.BBVA,
            statement_type=StatementType.CREDIT,
            new_format=False,
            start_phrase=['movimientos', 'efectuados'],
            end_phrase=['resumen', 'informativo', 'de', 'beneficios'],
            period_phrase=['en', 'el', 'periodo'],
            columns=['FECHA AUTORIZACION', 'FECHA APLICACION', 'CONCEPTO', 'R.F.C.', 'REFERENCIA', 'IMPORTE CARGOS', 'IMPORTE ABONOS'],
            amount_columns=AmountColumns(
                income='IMPORTE ABONOS',
                expense='IMPORTE CARGOS',
                balance=None,
                all_list=['IMPORTE CARGOS', 'IMPORTE ABONOS']
            ),
            date_pattern=r"(\d{2})/(\d{2})/(\d{2})",
            date_groups=DateGroups(year=3, month=2, day=1),
            month_pattern=MONTH_PATTERNS.num_to_abbr,
            amount_signs=AmountSigns(
                income=AmountSignType.NEUTRAL,
                expense=AmountSignType.NEUTRAL
            ),
            period_pattern=r'(\d{2})/(\d{2})/(\d{2})',
            period_month_pattern=None,
            period_group=DateGroups(year=3, month=2, day=1)
        )

    @classmethod
    def _register_bbva_credit_new(cls):
        """Register BBVA credit new format properties"""
        cls._registry[(BankName.BBVA, StatementType.CREDIT, True)] = BankProperties(
            bank=BankName.BBVA,
            statement_type=StatementType.CREDIT,
            new_format=True,
            start_phrase=['cargos,compras', 'y', 'abonos'],
            end_phrase=['total', 'cargos'],
            period_phrase=['tu', 'pago', 'requerido', 'este', 'periodo'],
            columns=['Fecha de la operación', 'Fecha de cargo', 'Descripción del movimiento', 'Monto'],
            amount_columns=AmountColumns(
                income='Monto',
                expense='Monto',
                balance=None,
                all_list=['Monto']
            ),
            date_pattern=r"(\d{2})-(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)-(20\d{2})",
            date_groups=DateGroups(year=3, month=2, day=1),
            month_pattern= {month.lower() : num for num, month in MONTH_PATTERNS.num_to_abbr.items()},
            amount_signs=AmountSigns(
                income=AmountSignType.NEGATIVE,
                expense=AmountSignType.POSITIVE
            ),
            period_pattern=r'(\d{2})-(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)-(\d{4})',
            period_month_pattern={k.lower() : v for k, v in MONTH_PATTERNS.abbr_to_num.items()},
            period_group=DateGroups(year=3, month=2, day=1)
        )

    @classmethod
    def _register_banamex_credit_old(cls):
        """Register Banamex credit old format properties"""
        cls._registry[(BankName.BANAMEX, StatementType.CREDIT, False)] = BankProperties(
            bank=BankName.BANAMEX,
            statement_type=StatementType.CREDIT,
            new_format=False,
            start_phrase=['detalle', 'de', 'operaciones'],
            end_phrase=['mensualidad*', 'aplica', 'para', 'compras', 'a', 'plazos.'],
            period_phrase=['fecha', 'de', 'corte'],
            columns=['Fecha', 'Concepto/Giro de Negocio Mensualidad * / Tipos de Cambio', 'Población / RFC Moneda Ext.', 'Otras Divisas', 'Pesos'],
            amount_columns=AmountColumns(
                income='Pesos',
                expense='Pesos',
                balance=None,
                all_list=['Pesos']
            ),
            date_pattern=r"(Ene|Feb|Mar|Abr|May|Jun|Jul|Ago|Sep|Oct|Nov|Dic) (\d{2})",
            date_groups=DateGroups(month=1, day=2),
            month_pattern={month.capitalize() : num for num, month in MONTH_PATTERNS.num_to_abbr.items()},
            amount_signs=AmountSigns(
                income=AmountSignType.NEGATIVE,
                expense=AmountSignType.NEUTRAL
            ),
            period_pattern=r'(\d{2}) (de) (enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre) (de) (\d{4})',
            period_month_pattern={k.lower() : v for k, v in MONTH_PATTERNS.month_to_num.items()},
            period_group=DateGroups(year=5, month=3, day=1)
        )

    @classmethod
    def _register_banamex_credit_new(cls):
        """Register Banamex credit new format properties"""
        cls._registry[(BankName.BANAMEX, StatementType.CREDIT, True)] = BankProperties(
            bank=BankName.BANAMEX,
            statement_type=StatementType.CREDIT,
            new_format=True,
            start_phrase=['cargos,', 'abonos', 'y', 'compras', 'regulares'],
            end_phrase=['total', 'cargos'],
            period_phrase=['tu', 'pago', 'requerido', 'este', 'periodo'],
            columns=['Fecha de la operación', 'Fecha de cargo', 'Descripción del movimiento', 'Monto'],
            amount_columns=AmountColumns(
                income='Monto',
                expense='Monto',
                balance=None,
                all_list=['Monto']
            ),
            date_pattern=r"(\d{2})-(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)-(20\d{2})",
            date_groups=DateGroups(year=3, month=2, day=1),
            month_pattern= {month.lower() : num for num, month in MONTH_PATTERNS.num_to_abbr.items()},
            amount_signs=AmountSigns(
                income=AmountSignType.NEGATIVE,
                expense=AmountSignType.POSITIVE
            ),
            period_pattern=r'(\d{2})-(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)-(\d{4})',
            period_month_pattern={k.lower() : v for k, v in MONTH_PATTERNS.abbr_to_num.items()},
            period_group=DateGroups(year=3, month=2, day=1)
        )

    @classmethod
    def _register_hsbc_credit(cls):
        """Register HSBC credit properties"""
        cls._registry[(BankName.HSBC, StatementType.CREDIT, False)] = BankProperties(
            bank=BankName.HSBC,
            statement_type=StatementType.CREDIT,
            new_format=False,
            start_phrase=['detalle', 'de', 'movimientos'],
            end_phrase=['información', "spei´s", 'recibidos'],
            period_phrase=['fecha', 'de', 'corte'],
            columns=['Fecha', 'Concepto', 'Importe'],
            amount_columns=AmountColumns(
                income='Importe',
                expense='Importe',
                balance=None,
                all_list=['Importe']
            ),
            date_pattern=r"(\d{2}) (ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC)",
            date_groups=DateGroups(month=2, day=1),
            month_pattern= MONTH_PATTERNS.abbr_to_num,
            amount_signs=AmountSigns(
                income=AmountSignType.NEGATIVE,
                expense=AmountSignType.NEUTRAL
            ),
            period_pattern=r"(\d{2}) (ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC) (\d{4})",
            period_month_pattern=MONTH_PATTERNS.abbr_to_num,
            period_group=DateGroups(year=3, month=2, day=1)
        )

    @classmethod
    def _register_inbursa_debit(cls):
        """Register Inbursa debit properties"""
        cls._registry[(BankName.INBURSA, StatementType.DEBIT, None)] = BankProperties(
            bank=BankName.INBURSA,
            statement_type=StatementType.DEBIT,
            new_format=None,
            start_phrase=['detalle', 'de', 'movimientos'],
            end_phrase=['movimientos', 'por', 'aclaracion'],
            initial_balance_phrase=['saldo', 'anterior'],
            final_balance_phrase=['saldo', 'actual'],
            initial_balance_description='BALANCE INICIAL',
            generated_amount_phrase=['rendimientos'],
            period_phrase=['periodo'],
            columns=['FECHA', 'REFERENCIA', 'CONCEPTO', 'CARGOS', 'ABONOS', 'SALDO'],
            amount_columns=AmountColumns(
                income='ABONOS',
                expense='CARGOS',
                balance='SALDO',
                all_list=['CARGOS', 'ABONOS', 'SALDO']
            ),
            date_pattern=r"(ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC) (\d{2})",
            date_groups=DateGroups(month=1, day=2),
            month_pattern= MONTH_PATTERNS.abbr_to_num,
            amount_signs=AmountSigns(
                income=AmountSignType.NEUTRAL,
                expense=AmountSignType.NEUTRAL
            ),
            period_pattern= r"(\d{2}) (Ene|Feb|Mar|Abr|May|Jun|Jul|Ago|Sep|Oct|Nov|Dic) (\d{4})",
            period_month_pattern={k.capitalize() : v for k, v in MONTH_PATTERNS.abbr_to_num.items()},
            period_group=DateGroups(year=3, month=2, day=1)
        )

    @classmethod
    def _register_inbursa_credit(cls):
        """Register Inbursa credit properties"""
        cls._registry[(BankName.INBURSA, StatementType.CREDIT, False)] = BankProperties(
            bank=BankName.INBURSA,
            statement_type=StatementType.CREDIT,
            new_format=False,
            start_phrase=['movimientos', 'del', 'periodo'],
            end_phrase=['resumen', 'de', 'promociones', 'a', 'meses', 'sin', 'interes'],
            period_phrase=['resumen', 'del', 'periodo'],
            columns=['Fecha', 'Descripción', 'Cantidad (pesos)'],
            amount_columns=AmountColumns(
                income='Cantidad (pesos)',
                expense='Cantidad (pesos)',
                balance=None,
                all_list=['Cantidad (pesos)']
            ),
            date_pattern=r"(\d{2})/(\d{2})",
            date_groups=DateGroups(month=1, day=2),
            month_pattern= MONTH_PATTERNS.num_to_abbr,
            amount_signs=AmountSigns(
                income=AmountSignType.NEGATIVE,
                expense=AmountSignType.NEUTRAL
            ),
            period_pattern= r"(\d{2}) (ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC) (\d{4})",
            period_month_pattern=MONTH_PATTERNS.abbr_to_num,
            period_group=DateGroups(year=3, month=2, day=1)
        )

    @classmethod
    def _register_nu_debit(cls):
        """Register NU debit properties"""
        cls._registry[(BankName.NU, StatementType.DEBIT, None)] = BankProperties(
            bank=BankName.NU,
            statement_type=StatementType.DEBIT,
            new_format=None,
            start_phrase=['detalle', 'de', 'movimientos', 'en', 'tu', 'cuenta'],
            end_phrase=['con', 'estos', 'movimientos,'],
            initial_balance_phrase=['saldo', 'inicial'],
            final_balance_phrase=['saldo', 'al', 'generar', 'este', 'estado', 'de', 'cuenta'],
            initial_balance_description=None,
            generated_amount_phrase=['dinero', 'generado', 'este', 'mes'],
            period_phrase=['periodo'],
            columns=[
                'FECHA',
                r'(DE) (\d{2}) (ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC) (A) (\d{2}) (ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC) (\(\d{2}) (DÍAS\))',
                'MONTO EN PESOS MEXICANOS'
            ],
            amount_columns=AmountColumns(
                income='MONTO EN PESOS MEXICANOS',
                expense='MONTO EN PESOS MEXICANOS',
                balance=None,
                all_list=['MONTO EN PESOS MEXICANOS']
            ),
            date_pattern=r"(\d{2}) (ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC) (20\d{2})?",
            date_groups=DateGroups(year=3, month=2, day=1),
            month_pattern= MONTH_PATTERNS.abbr_to_num,
            amount_signs=AmountSigns(
                income=AmountSignType.POSITIVE,
                expense=AmountSignType.NEGATIVE
            ),
            period_pattern= r"(\d{2}) (ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic) (20\d{2})",
            period_month_pattern={k.lower() : v for k, v in MONTH_PATTERNS.abbr_to_num.items()},
            period_group=DateGroups(year=3, month=2, day=1),
            special_data_filtering=NuSpecialDataFiltering()
        )

    @classmethod
    def _register_nu_credit(cls):
        """Register NU credit properties"""
        cls._registry[(BankName.NU, StatementType.CREDIT, False)] = BankProperties(
            bank=BankName.NU,
            statement_type=StatementType.CREDIT,
            new_format=False,
            start_phrase=['transacciones'],
            end_phrase=['información', 'de', 'costos'],
            period_phrase=['periodo'],
            columns=[
                'TRANSACCIONES',
                r'(DE) (\d{2}) (ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC) (A) (\d{2}) (ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC) (\(\d{2}) (DÍAS\))',
                'MONTOS EN PESOS MEXICANOS'
            ],
            amount_columns=AmountColumns(
                income='MONTOS EN PESOS MEXICANOS',
                expense='MONTOS EN PESOS MEXICANOS',
                balance=None,
                all_list=['MONTOS EN PESOS MEXICANOS']
            ),
            date_pattern=r"(\d{2}) (ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC)",
            date_groups=DateGroups(month=2, day=1),
            month_pattern= MONTH_PATTERNS.abbr_to_num,
            amount_signs=AmountSigns(
                income=AmountSignType.NEGATIVE,
                expense=AmountSignType.NEUTRAL
            ),
            period_pattern=r'(\d{2}) (ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC) (\d{4})',
            period_month_pattern=MONTH_PATTERNS.abbr_to_num,
            period_group=DateGroups(year=3, month=2, day=1)
        )

    @classmethod
    def _register_bank_configurations(cls, bank: BankName, statement_type: StatementType):
        """
        Register all configurations for a specific bank and statement type.
        This method is called lazily when properties are first requested.
        """
        if bank == BankName.BANORTE:
            if statement_type == StatementType.DEBIT:
                cls._register_banorte_debit()
            elif statement_type == StatementType.CREDIT:
                cls._register_banorte_credit_old()
                cls._register_banorte_credit_new()
        elif bank == BankName.BBVA:
            if statement_type == StatementType.DEBIT:
                cls._register_bbva_debit()
            elif statement_type == StatementType.CREDIT:
                cls._register_bbva_credit_old()
                cls._register_bbva_credit_new()
        elif bank == BankName.BANAMEX and statement_type == StatementType.CREDIT:
            cls._register_banamex_credit_old()
            cls._register_banamex_credit_new()
        elif bank == BankName.HSBC and statement_type == StatementType.CREDIT:
            cls._register_hsbc_credit()
        elif bank == BankName.INBURSA:
            if statement_type == StatementType.DEBIT:
                cls._register_inbursa_debit()
            elif statement_type == StatementType.CREDIT:
                cls._register_inbursa_credit()
        elif bank == BankName.NU:
            if statement_type == StatementType.DEBIT:
                cls._register_nu_debit()
            elif statement_type == StatementType.CREDIT:
                cls._register_nu_credit()
        else:
            raise ValueError(f"Bank: {bank} not supported")

    @classmethod
    def get_bank_properties(
            cls, 
            bank: BankName, 
            statement_type: StatementType, 
            new_format: bool | None = None
        ) -> BankProperties:
        """
        Get bank properties for the specified bank and statement type.
        Uses lazy loading to register only the needed configurations.
        
        Args:
            bank: Bank name as BankName enum
            statement_type: Statement type as StatementType enum
            new_format: Whether to use new format (True), old format (False), or any format (None)
            
        Returns:
            BankProperties instance
            
        Raises:
            ValueError: If bank or statement_type is invalid or properties not found
        """
        if not isinstance(bank, BankName):
            raise ValueError(f"Invalid bank name: {bank}. Valid options: {[b.value for b in BankName]}")
        
        if not isinstance(statement_type, StatementType):
            raise ValueError(f"Invalid statement type: {statement_type}. Valid options: {[s.value for s in StatementType]}")
        
        # Register configurations for this bank and statement type if not already registered
        try:
            cls._register_bank_configurations(bank, statement_type)
        except ValueError as e:
            raise ValueError(f"Failed to register bank configurations: {e}")
        
        # Try to find exact match first
        key = (bank, statement_type, new_format)
        if key in cls._registry:
            return cls._registry[key]
        
        # If new_format is specified but not found, try without format specification
        if new_format is not None:
            key = (bank, statement_type, None)
            if key in cls._registry:
                return cls._registry[key]
        
        # Provide more specific error message
        format_msg = f" with new_format={new_format}" if new_format is not None else ""
        raise ValueError(f"No properties found for bank {bank.value} and statement type {statement_type.value}{format_msg}")
