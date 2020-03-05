from django.http import JsonResponse

from .models import DTE

def GenerateAutoNumFact(request, compania, tipo, response_http=True):
    """
    Funcion para generar el numero de factura automaticamente

    @author Rodrigo Boet (rodrigo.b at timgla.com)
    @date 29-02-2020
    @param campania Recibe el valor de la compania
    @return new_num_dte numero de factura
    """
    if int(tipo) == 33:
        initial_def_dte = 'FE'
    elif int(tipo) == 39:
        initial_def_dte = 'BE'
    elif int(tipo) == 52:
        initial_def_dte = 'GDE'
    elif int(tipo) == 56:
        initial_def_dte = 'NDE'
    elif int(tipo) == 61:
        initial_def_dte = 'NCE'

    dte = DTE.objects.filter(compania=compania, tipo_dte=tipo)
    count_record = dte.count()
    last_record = dte.last()
    try:
        curr_dte = [digit for digit in last_record.numero_factura if digit.isdigit()]
        new_num_dte = int(''.join(curr_dte)) + 1
        count_new_dte = len(str(new_num_dte))
        new_num_dte = initial_def_dte + ''.join(curr_dte[:-count_new_dte]) + str(new_num_dte)
    except Exception as e:
        print(e)
        new_num_dte = initial_def_dte + '00001'

    if response_http:
        return JsonResponse({'num_dte': new_num_dte})
    return new_num_dte
