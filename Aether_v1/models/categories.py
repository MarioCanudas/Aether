from enum import Enum

class CategoryGroup(str, Enum):
    HOGAR = 'Hogar'
    TRANSPORTE = 'Transporte'
    ALIMENTACION = 'Alimentación'
    OCIO = 'Ocio'
    SALUD = 'Salud'
    FINANZAS = 'Finanzas'
    SERVICIOS = 'Servicios'
    INGRESOS = 'Ingresos'
    OTROS = 'Otros'
    
    