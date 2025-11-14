# Signet Verification API

Signet Verification is a receipt verification system that utilizes OCR and QR code scanning to verify transactions. It is designed to detect and prevent scams by identifying and flagging suspicious transactions.

## How it works

Users scan receipts using the Signet Verification App. The app uses OCR to extract text from the receipt and QR code scanning to extract the transaction details. The extracted information is then compared to verify the authenticity of the transaction.

If the transaction is not verified, the app logs the information and sends it to the server for analysis.

The server analyzes the extracted information to detect trends involving recurrent scammer details. If a trend is detected, the server sends an email to the verified account owner warning them that their receipt may have been used in a scam.
