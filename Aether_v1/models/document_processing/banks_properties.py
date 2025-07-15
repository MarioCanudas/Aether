from enum import Enum
from pydantic import BaseModel, field_validator
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple, TypedDict, Union

class BankType(str, Enum):
    AMEX = 'amex'
    BANORTE = 'banorte'
    BBVA = 'bbva'
    BANAMEX = 'banamex'
    HSBC = 'hsbc'
    INBURSA = 'inbursa'
    NU = 'nu'
    SANTANDER = 'santander'
    
BANKS_CODES = {
    '002': 'banamex',
    '006': 'bancomext',
    '009': 'banobras',
    '012': 'bbva',
    '014': 'santander',
    '019': 'banjercito',
    '021': 'hsbc',
    '030': 'bajio',
    '032': 'ixe',
    '036': 'inbursa',
    '037': 'interacciones',
    '042': 'mifel',
    '044': 'scotiabank',
    '058': 'banregio',
    '059': 'invex',
    '060': 'bansi',
    '062': 'afirme',
    '072': 'banorte',
    '102': 'the royal bank',
    '103': 'amex',
    '106': 'bamsa',
    '108': 'tokyo',
    '110': 'jp morgan',
    '112': 'bmonex',
    '113': 've por mas',
    '116': 'ing',
    '124': 'deutsche',
    '126': 'credit suisse',
    '127': 'azteca',
    '128': 'autofin',
    '129': 'barclays',
    '130': 'compartamos',
    '131': 'banco famsa',
    '132': 'bmultiva',
    '133': 'actinver',
    '134': 'wal-mart',
    '135': 'nafin',
    '136': 'interbanco',
    '137': 'bancoppel',
    '138': 'abc capital',
    '139': 'ubs bank',
    '140': 'consubanco',
    '141': 'volkswagen',
    '143': 'cibanco',
    '145': 'bbase',
    '166': 'bansefi',
    '168': 'hipotecaria federal',
    '600': 'monexcb',
    '601': 'gbm',
    '602': 'masari',
    '605': 'value',
    '606': 'estructuradores',
    '607': 'tiber',
    '608': 'vector',
    '610': 'b&b',
    '614': 'accival',
    '615': 'merrill lynch',
    '616': 'finamex',
    '617': 'valmex',
    '618': 'unica',
    '619': 'mapfre',
    '620': 'profuturo',
    '621': 'cb actinver',
    '622': 'oactin',
    '623': 'skandia',
    '626': 'cbdeutsche',
    '627': 'zurich',
    '628': 'zurichvi',
    '629': 'su casita',
    '630': 'cb intercam',
    '631': 'ci bolsa',
    '632': 'bulltick cb',
    '633': 'sterling',
    '634': 'fincomun',
    '636': 'hdi seguros',
    '637': 'order',
    '638': 'nu',
    '640': 'cb jpmorgan',
    '642': 'reforma',
    '646': 'stp',
    '647': 'telecomm',
    '648': 'evercore',
    '649': 'skandia',
    '651': 'segmty',
    '652': 'asea',
    '653': 'kuspit',
    '655': 'sofiexpress',
    '656': 'unagra',
    '659': 'opciones empresariales del noroeste',
    '670': 'libertad',
    '901': 'cls',
    '902': 'indeval',
    '999': 'n/a',
}
    
class StatementType(str, Enum):
    CREDIT = 'credit'
    DEBIT = 'debit'
    
class DateGroups(TypedDict):
    year: Optional[int] = None
    month: int
    day: int
    
@dataclass(frozen=True)
class MonthPatterns:
    # Abbreviated month names to numeric month names
    abbr_to_num: Dict[str, str] # e.g. 'ENE' -> '01'
    # Numeric month names to abbreviated month names
    num_to_abbr: Dict[str, str] # e.g. '01' -> 'ENE'
    
    def __post_init__(self):
        for abbr, num in self.abbr_to_num.items():
            if not self.num_to_abbr[num] == abbr:
                raise ValueError(f"Month pattern mismatch: {abbr} -> {num} and {num} -> {self.num_to_abbr[num]}")

month_patterns = MonthPatterns(
    num_to_abbr = {
        '01': 'ENE',
        '02': 'FEB',
        '03': 'MAR',
        '04': 'ABR',
        '05': 'MAY',
        '06': 'JUN',
        '07': 'JUL',
        '08': 'AGO',
        '09': 'SEP',
        '10': 'OCT',
        '11': 'NOV',
        '12': 'DIC'
    },
    
    abbr_to_num = {
        'ENE': '01',
        'FEB': '02',
        'MAR': '03',
        'ABR': '04',
        'MAY': '05',
        'JUN': '06',
        'JUL': '07',
        'AGO': '08',
        'SEP': '09',
        'OCT': '10',
        'NOV': '11',
        'DIC': '12'
    }
)
    
class AmountSignType(Enum):
    POSITIVE = '+'
    NEGATIVE = '-'
    NEUTRAL = None
    
class BankProperties(BaseModel):
    bank: BankType
    statement_type: StatementType
    new_format: Optional[bool] = None
    
    start_phrase: List[str]
    end_phrase: List[str]
    period_phrase: Optional[List[str]] = None
    initial_balance_phrase: Optional[List[str]] = None
    initial_balance_description: Optional[str] = None
    
    columns: List[str]
    amount_column: List[str]
    income_column: Optional[str] = None
    expense_column: Optional[str] = None
    balance_column: Optional[str] = None
    
    date_pattern: str
    date_groups: DateGroups
    month_pattern: Dict[str, str]
    
    income_sign: AmountSignType
    expense_sign: AmountSignType
    
    period_pattern: Optional[str] = None
    year_group: Optional[int] = None

    @field_validator('date_groups')
    @classmethod
    def validate_date_groups(cls, v):
        """Validate that date_groups contains required fields and valid values"""
        if not isinstance(v, dict):
            raise ValueError('date_groups must be a dictionary')
        if 'month' not in v or 'day' not in v:
            raise ValueError('date_groups must contain month and day')
        if not isinstance(v['month'], int) or not isinstance(v['day'], int):
            raise ValueError('month and day must be integers')
        if v['month'] < 1 or v['month'] > 12:
            raise ValueError('month must be between 1 and 12')
        if v['day'] < 1 or v['day'] > 31:
            raise ValueError('day must be between 1 and 31')
        if v.get('year') is not None and not isinstance(v['year'], int):
            raise ValueError('year must be an integer if provided')
        return v

    @field_validator('month_pattern')
    @classmethod
    def validate_month_pattern(cls, v):
        """Validate that month_pattern is a dictionary"""
        if not isinstance(v, dict):
            raise ValueError('month_pattern must be a dictionary')
        return v

    @field_validator('period_phrase')
    @classmethod
    def validate_period_phrase(cls, v):
        """Validate that period_phrase is a list"""
        if v is None:
            return []
        if not isinstance(v, list):
            raise ValueError('period_phrase must be a list')
        return v

    @field_validator('start_phrase', 'end_phrase')
    @classmethod
    def validate_phrases(cls, v):
        """Validate that phrases are lists of strings"""
        if not isinstance(v, list):
            raise ValueError('Phrases must be lists')
        if not all(isinstance(item, str) for item in v):
            raise ValueError('All phrase items must be strings')
        return v

    @field_validator('columns', 'amount_column')
    @classmethod
    def validate_columns(cls, v):
        """Validate that columns are lists of strings"""
        if not isinstance(v, list):
            raise ValueError('Columns must be lists')
        if not all(isinstance(item, str) for item in v):
            raise ValueError('All column items must be strings')
        return v

    @field_validator('date_pattern')
    @classmethod
    def validate_date_pattern(cls, v):
        """Validate that date_pattern is a non-empty string"""
        if not isinstance(v, str) or not v.strip():
            raise ValueError('date_pattern must be a non-empty string')
        return v

    @field_validator('income_sign', 'expense_sign')
    @classmethod
    def validate_amount_sign(cls, v):
        """Validate that amount sign is a valid AmountSignType"""
        if isinstance(v, AmountSignType):
            return v
        elif isinstance(v, str):
            try:
                return AmountSignType(v)
            except ValueError:
                raise ValueError(f'Invalid amount sign: {v}. Valid options: {[s.value for s in AmountSignType]}')
        elif v is None:
            return AmountSignType.NEUTRAL
        else:
            raise ValueError(f'Amount sign must be AmountSignType, string, or None, got {type(v)}')

    # Utility methods
    def get_amount_columns(self) -> List[str]:
        """Get all amount columns"""
        return self.amount_column
    
    def get_income_columns(self) -> List[str]:
        """Get income columns"""
        if self.income_column:
            return [self.income_column]
        return []
    
    def get_expense_columns(self) -> List[str]:
        """Get expense columns"""
        if self.expense_column:
            return [self.expense_column]
        return []
    
    def get_balance_columns(self) -> List[str]:
        """Get balance columns"""
        if self.balance_column:
            return [self.balance_column]
        return []
    
    def is_new_format(self) -> bool:
        """Check if this is a new format statement"""
        return self.new_format is True
    
    def get_date_group(self, group_type: str) -> Optional[int]:
        """Get a specific date group"""
        return self.date_groups.get(group_type)
    
    def get_month_mapping(self, direction: str = 'abbr_to_num') -> Dict[str, str]:
        """Get month mapping in the specified direction"""
        return getattr(self.month_pattern, direction, {})

class BankPropertiesFactory:
    """
    Factory class for creating and managing bank properties.
    Uses lazy loading to register only the properties that are actually needed.
    """
    
    _registry: Dict[Tuple[BankType, StatementType, Optional[bool]], BankProperties] = {}

    @classmethod
    def _register_banorte_debit(cls):
        """Register Banorte debit properties"""
        cls._registry[(BankType.BANORTE, StatementType.DEBIT, None)] = BankProperties(
            bank=BankType.BANORTE,
            statement_type=StatementType.DEBIT,
            new_format=None,
            start_phrase=['detalle', 'de', 'movimientos', '(pesos)▼'],
            end_phrase=['inversión', 'enlace', 'personal'],
            initial_balance_phrase=['saldo', 'inicial', 'del', 'periodo'],
            initial_balance_description='SALDO ANTERIOR',
            period_phrase=['periodo'],
            columns=['FECHA', 'DESCRIPCIÓN / ESTABLECIMIENTO', 'MONTO DEL DEPOSITO', 'MONTO DEL RETIRO', 'SALDO'],
            amount_column=['MONTO DEL DEPOSITO', 'MONTO DEL RETIRO', 'SALDO'],
            income_column='MONTO DEL DEPOSITO',
            expense_column='MONTO DEL RETIRO',
            balance_column='SALDO',
            date_pattern=r"(\d{2})-(\w{3})-(\d{2})",
            date_groups={'year': 3, 'month': 2, 'day': 1},
            month_pattern= month_patterns.abbr_to_num,
            income_sign=AmountSignType.NEUTRAL,
            expense_sign=AmountSignType.NEUTRAL,
            period_pattern=r"(\d{2})/(Enero|Febrero|Marzo|Abril|Mayo|Junio|Julio|Agosto|Septiembre|Octubre|Noviembre|Diciembre)/(\d{4})",
            year_group=3
        )

    @classmethod
    def _register_banorte_credit_old(cls):
        """Register Banorte credit old format properties"""
        cls._registry[(BankType.BANORTE, StatementType.CREDIT, False)] = BankProperties(
            bank=BankType.BANORTE,
            statement_type=StatementType.CREDIT,
            new_format=False,
            start_phrase=['detalle', 'de', 'movimientos', 'del' ,'titular',  'en', 'm.n.'],
            end_phrase=['si', 'solo', 'realizas', 'el', 'pago', 'mínimo'],
            period_phrase=['periodo'],
            columns=['Fecha', 'Concepto', 'RFC/CURP', 'Tipo de transacción', 'Importe'],
            amount_column=['Importe'],
            income_column='Importe',
            expense_column='Importe',
            date_pattern=r"(\d{2})/(\d{2})",
            date_groups={'year': None, 'month': 2, 'day': 1},
            month_pattern=month_patterns.abbr_to_num,
            income_sign=AmountSignType.NEGATIVE,
            expense_sign=AmountSignType.NEUTRAL,
            period_pattern=None,
            year_group=None
        )

    @classmethod
    def _register_banorte_credit_new(cls):
        """Register Banorte credit new format properties"""
        cls._registry[(BankType.BANORTE, StatementType.CREDIT, True)] = BankProperties(
            bank=BankType.BANORTE,
            statement_type=StatementType.CREDIT,
            new_format=True,
            start_phrase=['cargos,', 'abonos', 'y', 'compras', 'regulares'],
            end_phrase=['total', 'cargos'],
            period_phrase= None,
            columns=['Fecha de la operación', 'Fecha de cargo', 'Descripción del movimiento', 'Monto'],
            amount_column=['Monto'],
            date_pattern=r"(\d{2})-(ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC)-(20\d{2})",
            date_groups={'year': 3, 'month': 2, 'day': 1},
            month_pattern=month_patterns.abbr_to_num,
            income_sign=AmountSignType.NEGATIVE,
            expense_sign=AmountSignType.POSITIVE,
            period_pattern=None,
            year_group=None
        )

    @classmethod
    def _register_bbva_debit(cls):
        """Register BBVA debit properties"""
        cls._registry[(BankType.BBVA, StatementType.DEBIT, None)] = BankProperties(
            bank=BankType.BBVA,
            statement_type=StatementType.DEBIT,
            new_format=None,
            start_phrase=["detalle", "de", "movimientos", "realizados"],
            end_phrase=["le", "informamos", "que", "puede"],
            initial_balance_phrase=['saldo', 'anterior'],
            initial_balance_description=None,
            period_phrase=['periodo'],
            columns=['OPER', 'LIQ', 'DESCRIPCION', 'REFERENCIA', 'CARGOS', 'ABONOS', 'OPERACION', 'LIQUIDACION'],
            amount_column=['CARGOS', 'ABONOS', 'OPERACION', 'LIQUIDACION'],
            income_column='ABONOS',
            expense_column='CARGOS',
            balance_column='LIQUIDACION',
            date_pattern=r"^(\d{2})/([A-Z]{3})\b",
            date_groups={'year': None, 'month': 2, 'day': 1},
            month_pattern=month_patterns.abbr_to_num,
            income_sign=AmountSignType.NEUTRAL,
            expense_sign=AmountSignType.NEUTRAL,
            period_pattern=r"(\d{2})/(\d{2})/(\d{4})",
            year_group=3
        )

    @classmethod
    def _register_bbva_credit_old(cls):
        """Register BBVA credit old format properties"""
        cls._registry[(BankType.BBVA, StatementType.CREDIT, False)] = BankProperties(
            bank=BankType.BBVA,
            statement_type=StatementType.CREDIT,
            new_format=False,
            start_phrase=['movimientos', 'efectuados'],
            end_phrase=['resumen', 'informativo', 'de', 'beneficios'],
            period_phrase=None,
            columns=['FECHA AUTORIZACION', 'FECHA APLICACION', 'CONCEPTO', 'R.F.C.', 'REFERENCIA', 'IMPORTE CARGOS', 'IMPORTE ABONOS'],
            amount_column=['IMPORTE CARGOS', 'IMPORTE ABONOS'],
            income_column='IMPORTE ABONOS',
            expense_column='IMPORTE CARGOS',
            date_pattern=r"(\d{2})/(\d{2})/(\d{2})",
            date_groups={'year': 3, 'month': 2, 'day': 1},
            month_pattern=month_patterns.num_to_abbr,
            income_sign=AmountSignType.NEUTRAL,
            expense_sign=AmountSignType.NEUTRAL,
            period_pattern=None,
            year_group=None
        )

    @classmethod
    def _register_bbva_credit_new(cls):
        """Register BBVA credit new format properties"""
        cls._registry[(BankType.BBVA, StatementType.CREDIT, True)] = BankProperties(
            bank=BankType.BBVA,
            statement_type=StatementType.CREDIT,
            new_format=True,
            start_phrase=['cargos,compras', 'y', 'abonos'],
            end_phrase=['total', 'cargos'],
            period_phrase=None,
            columns=['Fecha de la operación', 'Fecha de cargo', 'Descripción del movimiento', 'Monto'],
            amount_column=['Monto'],
            date_pattern=r"(\d{2})-(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)-(20\d{2})",
            date_groups={'year': 3, 'month': 2, 'day': 1},
            month_pattern= {month.lower() : num for num, month in month_patterns.num_to_abbr.items()},
            income_sign=AmountSignType.NEGATIVE,
            expense_sign=AmountSignType.POSITIVE,
            period_pattern=None,
            year_group=None
        )

    @classmethod
    def _register_banamex_credit_old(cls):
        """Register Banamex credit old format properties"""
        cls._registry[(BankType.BANAMEX, StatementType.CREDIT, False)] = BankProperties(
            bank=BankType.BANAMEX,
            statement_type=StatementType.CREDIT,
            new_format=False,
            start_phrase=['detalle', 'de', 'operaciones'],
            end_phrase=['mensualidad*', 'aplica', 'para', 'compras', 'a', 'plazos.'],
            period_phrase=['fecha', 'de', 'corte'],
            columns=['Fecha', 'Concepto/Giro de Negocio Mensualidad * / Tipos de Cambio', 'Población / RFC Moneda Ext.', 'Otras Divisas', 'Pesos'],
            amount_column=['Pesos'],
            income_column='Pesos',
            expense_column='Pesos',
            date_pattern=r"(Ene|Feb|Mar|Abr|May|Jun|Jul|Ago|Sep|Oct|Nov|Dic) (\d{2})",
            date_groups={'year': None, 'month': 1, 'day': 2},
            month_pattern={month.capitalize() : num for num, month in month_patterns.num_to_abbr.items()},
            income_sign=AmountSignType.NEGATIVE,
            expense_sign=AmountSignType.NEUTRAL,
            period_pattern=None,
            year_group=None
        )

    @classmethod
    def _register_banamex_credit_new(cls):
        """Register Banamex credit new format properties"""
        cls._registry[(BankType.BANAMEX, StatementType.CREDIT, True)] = BankProperties(
            bank=BankType.BANAMEX,
            statement_type=StatementType.CREDIT,
            new_format=True,
            start_phrase=['cargos,', 'abonos', 'y', 'compras', 'regulares'],
            end_phrase=['total', 'cargos'],
            period_phrase=None,
            columns=['Fecha de la operación', 'Fecha de cargo', 'Descripción del movimiento', 'Monto'],
            amount_column=['Monto'],
            date_pattern=r"(\d{2})-(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)-(20\d{2})",
            date_groups={'year': 3, 'month': 2, 'day': 1},
            month_pattern= {month.lower() : num for num, month in month_patterns.num_to_abbr.items()},
            income_sign=AmountSignType.NEGATIVE,
            expense_sign=AmountSignType.POSITIVE,
            period_pattern=None,
            year_group=None
        )

    @classmethod
    def _register_hsbc_credit(cls):
        """Register HSBC credit properties"""
        cls._registry[(BankType.HSBC, StatementType.CREDIT, False)] = BankProperties(
            bank=BankType.HSBC,
            statement_type=StatementType.CREDIT,
            new_format=False,
            start_phrase=['detalle', 'de', 'movimientos'],
            end_phrase=['información', "spei´s", 'recibidos'],
            period_phrase=['fecha', 'de', 'corte'],
            columns=['Fecha', 'Concepto', 'Importe'],
            amount_column=['Importe'],
            income_column='Importe',
            expense_column='Importe',
            date_pattern=r"(\d{2}) (ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC)",
            date_groups={'year': None, 'month': 2, 'day': 1},
            month_pattern= month_patterns.abbr_to_num,
            income_sign=AmountSignType.NEGATIVE,
            expense_sign=AmountSignType.NEUTRAL,
            period_pattern=None,
            year_group=None
        )

    @classmethod
    def _register_inbursa_debit(cls):
        """Register Inbursa debit properties"""
        cls._registry[(BankType.INBURSA, StatementType.DEBIT, None)] = BankProperties(
            bank=BankType.INBURSA,
            statement_type=StatementType.DEBIT,
            new_format=None,
            start_phrase=['detalle', 'de', 'movimientos'],
            end_phrase=['movimientos', 'por', 'aclaracion'],
            initial_balance_phrase=['saldo', 'anterior'],
            initial_balance_description='BALANCE INICIAL',
            period_phrase=['periodo'],
            columns=['FECHA', 'REFERENCIA', 'CONCEPTO', 'CARGOS', 'ABONOS', 'SALDO'],
            amount_column=['CARGOS', 'ABONOS', 'SALDO'],
            income_column='ABONOS',
            expense_column='CARGOS',
            balance_column='SALDO',
            date_pattern=r"(ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC) (\d{2})",
            date_groups={'year': None, 'month': 1, 'day': 2},
            month_pattern= month_patterns.abbr_to_num,
            income_sign=AmountSignType.NEUTRAL,
            expense_sign=AmountSignType.NEUTRAL,
            period_pattern=None,
            year_group=None
        )

    @classmethod
    def _register_inbursa_credit(cls):
        """Register Inbursa credit properties"""
        cls._registry[(BankType.INBURSA, StatementType.CREDIT, False)] = BankProperties(
            bank=BankType.INBURSA,
            statement_type=StatementType.CREDIT,
            new_format=False,
            start_phrase=['movimientos', 'del', 'periodo'],
            end_phrase=['resumen', 'de', 'promociones', 'a', 'meses', 'sin', 'interes'],
            period_phrase=['resumen', 'del', 'periodo'],
            columns=['Fecha', 'Descripción', 'Cantidad (pesos)'],
            amount_column=['Cantidad (pesos)'],
            income_column='Cantidad (pesos)',
            expense_column='Cantidad (pesos)',
            date_pattern=r"(\d{2})/(\d{2})",
            date_groups={'year': None, 'month': 1, 'day': 2},
            month_pattern= month_patterns.num_to_abbr,
            income_sign=AmountSignType.NEGATIVE,
            expense_sign=AmountSignType.NEUTRAL,
            period_pattern=None,
            year_group=None
        )

    @classmethod
    def _register_nu_debit(cls):
        """Register NU debit properties"""
        cls._registry[(BankType.NU, StatementType.DEBIT, None)] = BankProperties(
            bank=BankType.NU,
            statement_type=StatementType.DEBIT,
            new_format=None,
            start_phrase=['detalle', 'de', 'movimientos', 'en', 'tu', 'cuenta'],
            end_phrase=['con', 'estos', 'movimientos,'],
            initial_balance_phrase=['saldo', 'inicial'],
            initial_balance_description=None,
            period_phrase=None,
            columns=[
                'FECHA',
                r'(DE) (\d{2}) (ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC) (A) (\d{2}) (ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC) (\(\d{2}) (DÍAS\))',
                'MONTO EN PESOS MEXICANOS'
            ],
            amount_column=['MONTO EN PESOS MEXICANOS'],
            income_column='MONTO EN PESOS MEXICANOS',
            expense_column='MONTO EN PESOS MEXICANOS',
            date_pattern=r"(\d{2}) (ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC) (20\d{2})",
            date_groups={'year': 3, 'month': 2, 'day': 1},
            month_pattern= month_patterns.abbr_to_num,
            income_sign=AmountSignType.POSITIVE,
            expense_sign=AmountSignType.NEGATIVE,
            period_pattern=None,
            year_group=None
        )

    @classmethod
    def _register_nu_credit(cls):
        """Register NU credit properties"""
        cls._registry[(BankType.NU, StatementType.CREDIT, False)] = BankProperties(
            bank=BankType.NU,
            statement_type=StatementType.CREDIT,
            new_format=False,
            start_phrase=['transacciones'],
            end_phrase=['saldo', 'final', 'del', 'periodo'],
            period_phrase=['periodo'],
            columns=[
                'TRANSACCIONES',
                r'(DE) (\d{2}) (ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC) (A) (\d{2}) (ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC) (\(\d{2}) (DÍAS\))',
                'MONTOS EN PESOS MEXICANOS'
            ],
            amount_column=['MONTOS EN PESOS MEXICANOS'],
            income_column='MONTOS EN PESOS MEXICANOS',
            expense_column='MONTOS EN PESOS MEXICANOS',
            date_pattern=r"(\d{2}) (ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC)",
            date_groups={'year': None, 'month': 2, 'day': 1},
            month_pattern= month_patterns.abbr_to_num,
            income_sign=AmountSignType.NEGATIVE,
            expense_sign=AmountSignType.NEUTRAL,
            period_pattern=None,
            year_group=None
        )

    @classmethod
    def _register_bank_configurations(cls, bank: BankType, statement_type: StatementType):
        """
        Register all configurations for a specific bank and statement type.
        This method is called lazily when properties are first requested.
        """
        if bank == BankType.BANORTE:
            if statement_type == StatementType.DEBIT:
                cls._register_banorte_debit()
            elif statement_type == StatementType.CREDIT:
                cls._register_banorte_credit_old()
                cls._register_banorte_credit_new()
        elif bank == BankType.BBVA:
            if statement_type == StatementType.DEBIT:
                cls._register_bbva_debit()
            elif statement_type == StatementType.CREDIT:
                cls._register_bbva_credit_old()
                cls._register_bbva_credit_new()
        elif bank == BankType.BANAMEX and statement_type == StatementType.CREDIT:
            cls._register_banamex_credit_old()
            cls._register_banamex_credit_new()
        elif bank == BankType.HSBC and statement_type == StatementType.CREDIT:
            cls._register_hsbc_credit()
        elif bank == BankType.INBURSA:
            if statement_type == StatementType.DEBIT:
                cls._register_inbursa_debit()
            elif statement_type == StatementType.CREDIT:
                cls._register_inbursa_credit()
        elif bank == BankType.NU:
            if statement_type == StatementType.DEBIT:
                cls._register_nu_debit()
            elif statement_type == StatementType.CREDIT:
                cls._register_nu_credit()
        else:
            raise ValueError(f"Bank: {bank} not supported")

    @classmethod
    def get_bank_properties(
            cls, 
            bank: Union[str, BankType], 
            statement_type: Union[str, StatementType], 
            new_format: Optional[bool] = None
        ) -> BankProperties:
        """
        Get bank properties for the specified bank and statement type.
        Uses lazy loading to register only the needed configurations.
        
        Args:
            bank: Bank name as string or BankType enum
            statement_type: Statement type as string or StatementType enum
            new_format: Whether to use new format (True), old format (False), or any format (None)
            
        Returns:
            BankProperties instance
            
        Raises:
            ValueError: If bank or statement_type is invalid or properties not found
        """
        # Use validation methods for better error handling
        bank_enum = cls.validate_bank_enum(bank)
        statement_enum = cls.validate_statement_type_enum(statement_type)
        
        # Register configurations for this bank and statement type if not already registered
        try:
            cls._register_bank_configurations(bank_enum, statement_enum)
        except ValueError as e:
            raise ValueError(f"Failed to register bank configurations: {e}")
        
        # Try to find exact match first
        key = (bank_enum, statement_enum, new_format)
        if key in cls._registry:
            return cls._registry[key]
        
        # If new_format is specified but not found, try without format specification
        if new_format is not None:
            key = (bank_enum, statement_enum, None)
            if key in cls._registry:
                return cls._registry[key]
        
        # Provide more specific error message
        format_msg = f" with new_format={new_format}" if new_format is not None else ""
        raise ValueError(f"No properties found for bank {bank_enum.value} and statement type {statement_enum.value}{format_msg}")

    @classmethod
    def validate_bank_enum(cls, bank: Union[str, BankType]) -> BankType:
        """
        Validate and convert bank to BankType enum.
        
        Args:
            bank: Bank name as string or BankType enum
            
        Returns:
            BankType enum
            
        Raises:
            ValueError: If bank is invalid
        """
        if isinstance(bank, BankType):
            return bank
        elif isinstance(bank, str):
            try:
                return BankType(bank)
            except ValueError:
                raise ValueError(f"Invalid bank name: {bank}. Valid options: {[b.value for b in BankType]}")
        else:
            raise ValueError(f"Bank must be string or BankType enum, got {type(bank)}")

    @classmethod
    def validate_statement_type_enum(cls, statement_type: Union[str, StatementType]) -> StatementType:
        """
        Validate and convert statement_type to StatementType enum.
        
        Args:
            statement_type: Statement type as string or StatementType enum
            
        Returns:
            StatementType enum
            
        Raises:
            ValueError: If statement_type is invalid
        """
        if isinstance(statement_type, StatementType):
            return statement_type
        elif isinstance(statement_type, str):
            try:
                return StatementType(statement_type)
            except ValueError:
                raise ValueError(f"Invalid statement type: {statement_type}. Valid options: {[s.value for s in StatementType]}")
        else:
            raise ValueError(f"Statement type must be string or StatementType enum, got {type(statement_type)}")