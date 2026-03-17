#import Packages
import pandas as pd
import numpy as np
import datetime as dt
import requests as rq
from pathlib import Path
import xml.etree.ElementTree as ET

def treasury_xml_url(date: str = None):

    base_url = 'https://home.treasury.gov'
    endpoint = '/resource-center/data-chart-center/interest-rates/pages/xml'
    date_format = dt.datetime.strptime(date, "%m-%d-%Y").strftime("%Y%m")
    daily_treasury_rates_xml = f"{base_url}{endpoint}?data=daily_treasury_yield_curve&field_tdr_date_value_month={date_format}"
    return daily_treasury_rates_xml

def treasury_yields_import(
    date: str = None,
    maturities: list = None
) -> list[dict]:

    # Map Maturities
    MATURITY_MAP = {
        "BC_1MONTH": "1M",
        "BC_1_5MONTH": "1.5M",
        "BC_2MONTH": "2M",
        "BC_3MONTH": "3M",
        "BC_4MONTH": "4M",
        "BC_6MONTH": "6M",
        "BC_1YEAR": "1Y",
        "BC_2YEAR": "2Y",
        "BC_3YEAR": "3Y",
        "BC_5YEAR": "5Y",
        "BC_7YEAR": "7Y",
        "BC_10YEAR": "10Y",
        "BC_20YEAR": "20Y",
        "BC_30YEAR": "30Y",
    }

    # Define namespaces matching wihtin the XML feed
    NS = {
        "atom": "http://www.w3.org/2005/Atom",
        "d":    "http://schemas.microsoft.com/ado/2007/08/dataservices",
        "m":    "http://schemas.microsoft.com/ado/2007/08/dataservices/metadata",
    }
    #Initalize months checked dictionary
    months_checked = {}
    fmt        = "%m-%d-%Y"
    Lookback = 3
    results = {}
    #Create a set from the given yields, if statement is to check for user input maturities
    active_maturities = set(maturities) if maturities else set(MATURITY_MAP.values())
    #Turn user specified date into proper format, if no date input, return the curret date
    start_date = dt.datetime.strptime(date, fmt) if date else dt.datetime.today()

    #Begin with holiday/weekend handling for loop, initalize variables to cache data pulls based on the month, max run of 7 to prevent an infinite loop
    for m in range(Lookback):
        date_found = False
        current_search_date = start_date - dt.timedelta(days=m)
        month_key = current_search_date.strftime("%Y%m")
        date_str = current_search_date.strftime(fmt)

        #Checks to see if the current month has been searched, new xml pull initiated for the previous month
        if month_key not in months_checked:
            xml_pull = treasury_xml_url(date=date_str)
            response = rq.get(xml_pull)
            response.raise_for_status()
            #Sets the month_check to true once pulled
            months_checked[month_key] = True

        root = ET.fromstring(response.content)

        for entry in root.findall("atom:entry", NS):
            props = entry.find(".//m:properties", NS)
            if props is None:
                continue

                # Parse the date
            date_el = props.find("d:NEW_DATE", NS)
            if date_el is None or not date_el.text:
                continue

            try:
                # API returns ISO format: "2025-02-18T00:00:00"
                entry_date = dt.datetime.strptime(date_el.text.strip(), "%Y-%m-%dT%H:%M:%S")
            except ValueError:
                continue

            if entry_date != current_search_date.replace(hour=0, minute=0, second=0):
                continue

            #Date is found if code makes it past date search, update date_found ValueError
            date_found = True

            #Setup empty yields dict for which to store dictionary of yields for a given day
            yields = {}

            #Derive tags relating to maturities
            for tag, label in MATURITY_MAP.items():
                if label not in active_maturities:
                    continue
                #Pulls the d tag from the HTML atom structure
                el = props.find(f"d:{tag}", NS)
                if el is not None and el.text and el.text.strip():
                    try:
                        yields[label] = float(el.text.strip())
                    except ValueError:
                        continue

            if yields:
                results[entry_date.strftime(fmt)] = yields
            #Close inner loop, date has been found
            break

        if date_found:
            #Break outer loop once valid day found
            break
    return results
