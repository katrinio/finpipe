# Workflows

`run_invoice_delivery.py` generates the current Salary Invoice, sends the PDF to the requested Telegram chat, and deletes the PDF and intermediate DOCX in a `finally` block.

Document generation remains separate under `src/workflows/tasks/`. Generation attempts and outcomes are recorded in `DocumentGenerationHistory`.
