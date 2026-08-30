-- ==============================================================================
-- Populate card_product_name in banking-agent-rag-mcp.banking_data.credit_cards
-- Allowed values: 'Premier', 'Taj', 'Travel One', 'Live+', 'Visa Platinum'
-- Preserves all other existing column values unchanged.
-- ==============================================================================

UPDATE `banking-agent-rag-mcp.banking_data.credit_cards`
SET card_product_name = CASE MOD(ABS(FARM_FINGERPRINT(card_account_number)), 5)
  WHEN 0 THEN 'Premier'
  WHEN 1 THEN 'Taj'
  WHEN 2 THEN 'Travel One'
  WHEN 3 THEN 'Live+'
  ELSE 'Visa Platinum'
END
WHERE card_product_name IS NULL;
