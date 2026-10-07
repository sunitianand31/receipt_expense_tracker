RECEIPT_EXTRACTION_PROMPT = """
Analyze this receipt image carefully.

Extract the following information:

1. Store or shop name
2. Date of purchase
3. Total amount
4. Items purchased
5. Expense category

Return the result in this exact format:

Store: 
Date: 
Total: 
Items: 
Category: 

If any information is not visible, write "Not available".
"""