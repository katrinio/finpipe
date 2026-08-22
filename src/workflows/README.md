# Workflows

`run_invoice_delivery.py` generates the current Salary Invoice, sends the PDF to the requested Telegram chat, and deletes the PDF and intermediate DOCX in a `finally` block.

`run_bank_confirmation_delivery.py` generates a Bank Transfer Confirmation from an uploaded Telegram PDF. `run_conversion_request_delivery.py` generates a Conversion Request for the latest extracted bank amount. Both send their result to Telegram and remove temporary files in `finally` blocks.

Document generation remains separate under `src/workflows/tasks/`. Operational outcomes are written to the regular application log.
