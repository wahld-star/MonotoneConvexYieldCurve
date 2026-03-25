# Yield Curve Construction using various interpolation methods

This repository allows users to construct Yield Curves using various interpolation methods.<br>Data is retrieved via the US Department of Treasury historical treasury yield xml feed.<br>https://home.treasury.gov/sites/default/files/interest-rates/yield.xml

## Data Retrieval 
Historical data is retrieved via the UST_Prod.py file <br>

### Rates Retrieved:
>1 Month <br>1.5 Month<br> 2 Month<br> 3 Month<br> 4 Month<br> 6 Month<br> 1 Year<br> 2 Year<br> 3 Year<br> 5 Year<br> 7 Year<br> 10 Year<br> 20 Year<br> 30 Year

Packages Utilized:
- datetime
- requests
- xml.etree.ElementTree

Parameters:
- date -> The date parameter defines the value date for which the rates are pulled from the xml feed
- For weekends or holidays the previous business day will automatically be retrieved <br>



