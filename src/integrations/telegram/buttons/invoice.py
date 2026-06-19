class InvoiceMenuButtons:
    SET_INVOICE_AMOUNT = "💰 Указать сумму"
    GET_INVOICE_AMOUNT = "💶 Текущая сумма"
    GENERATE_INVOICE = "📄 Создать инвойс"
    SEND_TO_COMPANY = "📤 Отправить компании"

    CB_SEND_TO_COMPANY = "action:invoice_send"
    CB_SKIP_SEND = "action:invoice_skip"

    CB_SET_AMOUNT = "nav:set_amount"
    CB_GET_AMOUNT = "nav:get_amount"
    CB_GENERATE = "nav:generate_invoice"
    CB_BACK = "nav:documents"
