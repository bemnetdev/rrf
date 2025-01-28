new_columns = [
    'No', 
    'SHI Code',
    'Item',
    'Unit',
    'Category',
    'Beginning Balance',
    'Received Quantity (B1)',
    'Received Quantity (B2)',
    'Loss_Adjustment',
    'Ending Balance',
    'Days Out of Stock (DOS)',
    'Total Monthly Consumption',
    'Adjusted Monthly Consumption',
    'Adjusted AMC',
    'MOS',
    'Expiry Date',
    'Total suggested Qty needed to reach max',
    'Requested quantity By Faclity',
    'Qty refilled from EPSA',
    'Remark',
]


# List of columns to drop
columns_to_drop = [
    'Adjusted Monthly Consumption',
    'Total Monthly Consumption',
    'Adjusted AMC',
    'MOS',
    'Total suggested Qty needed to reach max',
    'Remark',
]


# Select columns to convert to integer
int_columns = [
    'Beginning Balance',
    'Received Quantity (B1)',
    'Received Quantity (B2)',
    'Loss_Adjustment',
    'Ending Balance',
    'Days Out of Stock (DOS)',
    'Requested quantity By Faclity',
    'Qty refilled from EPSA'
]


analysis_columns = [
    'S.No',
    'Item Managed by the Hub',
    'Account',
    'Item',
    'Unit',
    'SOH',
    'AMC',
    'Unit Price',
    'Total price',
    'Expiry Date',
    'Analysis Start Date (MM/DD/YY)',
    'Shelf Life in Month',
    'Issuable Shelf Life',
    'Max. Amount Can be Consumed till Expiry',
    'Amount in Unit of Measurement',
    'Amount in price',
    'Recommendation',
    'Maximum Stock Can be Received by this Batch'
]


an_cols_to_drop = [
    'Item Managed by the Hub',
    'Account',
    'Unit',
    'SOH',
    'AMC',
    'Total price',
    'Expiry Date',
    'Shelf Life in Month',
    'Issuable Shelf Life',
    'Max. Amount Can be Consumed till Expiry',
    'Amount in Unit of Measurement',
    'Amount in price',
    'Recommendation',
    'Maximum Stock Can be Received by this Batch'
]


columns_to_print = [
    'SHI Code',
    'Item',
    'Unit',
    'Category',
    'Beginning Balance',
    'Received Quantity (B1)',
    'Received Quantity (B2)',
    'Loss_Adjustment',
    'Ending Balance',
    'Days Out of Stock (DOS)'
]