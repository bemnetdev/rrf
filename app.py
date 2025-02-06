import streamlit as st
import re
import os
import pandas as pd
import numpy as np
import openpyxl
import time
from base_data import *
from datetime import datetime, date
from ethiopian_date import EthiopianDateConverter
from dotenv import load_dotenv
from sqlalchemy import create_engine, exc

# Load environment variables from .env file
load_dotenv()

st.title("RRF for Cancer Drugs")
st.text("By Opian Health")

show_content = st.checkbox("Show Guideline")
if show_content:
    st.header("File Upload Guidelines")
    st.write("""
    Vital (RRF) Report Sheet Data Postitioning
    - Health Facility Name at C4
    - Duration at C5
    - List of drugs starting from row 8
            
    Analysis Sheet Data Postitioning
    - List of drugs starting from row 5
    """)

show_input = True
input_container = st.empty()

# Get database credentials from environment variables
database_name = "RRF"
db_password = input_container.text_input("", placeholder="Enter the database password", type="password")
db_host = "196.189.119.104"


def detect_sheet(fpath):
    try:
        excel_file = pd.ExcelFile(fpath)
        sheet_names = excel_file.sheet_names
        if "Vital Report" in sheet_names:
            RRF = "Vital Report"
        elif "RRF-Report" in sheet_names:
            RRF = "RRF-Report"
        else:
            RRF = None
            print("RRF-Report could not be detected in the file you provide.")
            
        if "Non-PPL Additional  Request" in sheet_names:
            NPPL = "Non-PPL Additional  Request"
        elif "NPPL Additional Items Request" in sheet_names:
            NPPL = "NPPL Additional Items Request"
        else:
            NPPL = None
            print("Non-PPL could not be detected in the file you provide.")
            
        if "Analysis" in sheet_names:
            Analysis = "Analysis"
        else:
            Analysis = None
            print("Analysis could not be detected in the file you provide.")
            
        if "Patient Data" in sheet_names:
            Patient_Data = "Patient Data"
        elif "patient on treatment" in sheet_names:
            Patient_Data = "patient on treatment"
        elif "number of patients" in sheet_names:
            Patient_Data = "number of patients"
        else:
            Patient_Data = None
            print("Patient Data could not be detected in the file you provide.")
            
        return RRF, NPPL, Analysis, Patient_Data
    except:
        st.error("Unable to detect the sheets in the excel file!", icon="❌")


def load_data(path, sheet):
    try:
        df = pd.read_excel(path, sheet_name=sheet)
        return df
    except:
        st.error("Unable to load the data in ", sheet , " sheet!", icon="❌")


def extract_data(df):
    try:
        HF = df["Unnamed: 2"][2].title()
        HF = ' '.join(word.capitalize() for word in re.findall(r'\w+', HF))
        RP = df["Unnamed: 2"][3]
        if isinstance(RP, datetime):
            RP = RP.date()
            RP = RP.strftime('%d/%m/%Y')
        RP = RP.replace(" ", "")
        if '-' in RP:
            date_parts = RP.split('-')
        elif 'to' in RP:
            date_parts = RP.split('to')
        else:
            date_parts = [None, RP]
        SRP = date_parts[0]
        ERP = date_parts[1]
        return HF, SRP, ERP
    except:
        st.error("Unable to extract health facility name and duration in the excel file! Please follow the Guideline!", icon="❌")


def clean_data(df, new_columns, columns_to_drop, int_columns, HF, SRP, ERP):
    try:
        df_drop_1 = df.iloc[6:]
        df_drop_2 = df_drop_1[pd.to_numeric(df_drop_1[df_drop_1.columns[0]], errors='coerce').notnull()]
        remark_index = df_drop_2.columns.get_loc("Unnamed: 19")
        df_drop_2 = df_drop_2.iloc[:, :remark_index + 1]
        df_drop_2.columns = new_columns
        df_drop_2.set_index('No', inplace=True)
        df_drop_3 = df_drop_2.drop(columns=columns_to_drop)
        df_drop_3.insert(0, 'Health_Facility', HF)
        df_drop_3.insert(1, 'Start Reporting Period', SRP)
        df_drop_3.insert(2, 'Ending Reporting Period', ERP)
        df_drop_3['Expiry Date'] = df_drop_3['Expiry Date'].astype(str)
        df_drop_3['Expiry Date'] = df_drop_3['Expiry Date'].str.split(' ').str[0]
        for col in int_columns:
            df_drop_3[col] = pd.to_numeric(df_drop_3[col], errors='coerce').fillna(0).astype(int)
        return df_drop_3
    except:
        st.error("Unable to clean the RRF table data!", icon="❌")


def print_data(DFF):
    PData = DFF[columns_to_print]
    st.write(pd.concat([PData.head(), PData.tail()]))


def convert_date(eDate):
    try:
        if eDate != None:
            date_splitted = eDate.split('/')
            if len(date_splitted[2]) == 2:
                date_splitted[2] = "20" + str(date_splitted[2])
            ethiopian_year = int(date_splitted[2])
            ethiopian_month = int(date_splitted[1])
            ethiopian_day = int(date_splitted[0])
            gregorian_date = EthiopianDateConverter.to_gregorian(ethiopian_year, ethiopian_month, ethiopian_day)
            gDate = str(gregorian_date.day) + "/" + str(gregorian_date.month) + "/" + str(gregorian_date.year)
        else:
            gDate = eDate
        return gDate
    except:
        st.error("Unable to convert the Ethiopian date duration data to Gregorian calendar!", icon="❌")


def setup(new_columns, columns_to_drop, int_columns, fpath, engine):
    RRF, NPPL, Analysis, Patient_Data = detect_sheet(fpath)
    st.success("About the file you have uploaded...")
    st.write("RRF Report Sheet Name = ", RRF)
    st.write("NPPL Sheet Name = ", NPPL)
    st.write("Analysis Sheet Name = ", Analysis)
    st.write("Patient Data Sheet Name = ", Patient_Data)
    df = load_data(fpath, RRF)
    HF, SRP, ERP = extract_data(df)
    st.success("Data about the Request...")
    st.write("Health Facility:", HF)
    st.write("Duration: ", SRP, " E.C to ", ERP, " E.C")
    SRP = convert_date(SRP)
    ERP = convert_date(ERP)
    DFF = clean_data(df, new_columns, columns_to_drop, int_columns, HF, SRP, ERP)
    st.write(len(DFF), " Drugs Requested")
    st.success("Working on RRF table...")
    track = pd.DataFrame({'File_Name': [fpath.name], 'Health_Facility': [HF], 'Start_Date': [SRP], 'End_Date': [ERP], 'Data_Inserted_On': [datetime.now()]}, index=[0])

    query = 'SELECT "File_Name", "Health_Facility", "Start_Date", "End_Date" FROM public."Track"'
    existing_data = pd.read_sql(query, engine)
    data_exists = existing_data.equals(track.drop(columns=['Data_Inserted_On']))

    # If the data to be inserted is not already in the table, proceed with insertion
    if data_exists:
        st.error("You have loaded data from this file already!")
    else:
        print_data(DFF)

    return track, DFF, NPPL, Analysis, Patient_Data, HF, SRP, ERP, data_exists


def clean_analysis(analysis_df):
    try:
        analysis_df = analysis_df.iloc[3:]
        remark_index = analysis_df.columns.get_loc("Unnamed: 17")
        analysis_df = analysis_df.iloc[:, :remark_index + 1]
        analysis_df.columns = analysis_columns
        analysis_df.set_index('S.No', inplace=True)
        analysis_df['Analysis Start Date (MM/DD/YY)'] = pd.to_datetime(analysis_df['Analysis Start Date (MM/DD/YY)']).dt.date
        analysis_df['Unit Price'] = pd.to_numeric(analysis_df['Unit Price'], errors='coerce')
        analysis_clean = analysis_df.drop(columns=an_cols_to_drop)
        return analysis_clean
    except:
        st.error("Unable to clean the Analysis sheet data! Please follow the guideline!", icon="❌")


def analysis_table(fpath, Analysis):
    analysis_df = load_data(fpath, Analysis)
    analysis_clean = clean_analysis(analysis_df)
    st.write(pd.concat([analysis_clean.head(), analysis_clean.tail()]))
    return analysis_clean


def merge_rrf(DFF, analysis_clean):
    try:
        analysis_unique_items = analysis_clean['Item'].unique()
        rrf_filtered_rows = DFF[~DFF['Item'].isin(analysis_unique_items)]
        rrf_unique_items = DFF['Item'].unique()
        analysis_filtered_rows = analysis_clean[~analysis_clean['Item'].isin(rrf_unique_items)]
        RRF_Analysis = pd.merge(DFF, analysis_clean, on='Item', how='left')
        if len(rrf_filtered_rows) != 0:
            st.warning("List of Item which does not exists in the Analysis...", icon="⚠️")
            st.write(rrf_filtered_rows['Item'])
        if len(analysis_filtered_rows) != 0:
            st.warning("List of Item which does not exists in the RRF Report...", icon="⚠️")
            st.write(analysis_filtered_rows['Item'])
        return RRF_Analysis
    except:
        st.error("Unable to merge RRF Report sheet data and Analysis sheet data in the excel file!", icon="❌")


def nppl_clean(nppl_df, HF, SRP, ERP):
    try:
        remark_index = nppl_df.columns.get_loc("Quantity Requested")
        nppl_df = nppl_df.iloc[:, :remark_index + 1]
        nppl_df = nppl_df.rename(columns={'Unnamed: 0': 'S.No'})
        nppl_df.set_index('S.No', inplace=True)
        nppl_df['Expiry Date'] = pd.to_datetime(nppl_df['Expiry Date']).dt.date
        st.write(pd.concat([nppl_df.head(), nppl_df.tail()]))
        nppl_df.insert(0, 'Health_Facility', HF)
        nppl_df.insert(1, 'Start Reporting Period', SRP)
        nppl_df.insert(2, 'Ending Reporting Period', ERP)
        return nppl_df
    except:
        st.error("Unable to clean the NPPL sheet data!", icon="❌")


def nppl_table(fpath, NPPL, HF, SRP, ERP):
    nppl_df = load_data(fpath, NPPL)
    nppl_df = nppl_clean(nppl_df, HF, SRP, ERP)
    return nppl_df


def patient_clean(patient_df, HF, SRP, ERP):
    try:
        patient_df = patient_df.drop(columns=["Unnamed: 0", "Notes"])
        patient_df['Cancer Type'] = patient_df['Cancer Type'].fillna(method='ffill')
        st.write(pd.concat([patient_df.head(), patient_df.tail()]))
        patient_df.insert(0, 'Health_Facility', HF)
        patient_df.insert(1, 'Start Reporting Period', SRP)
        patient_df.insert(2, 'Ending Reporting Period', ERP)
        return patient_df
    except:
        st.error("Unable to clean the Patient sheet data!", icon="❌")


def patient_table(fpath, Patient_Data, HF, SRP, ERP):
    patient_df = load_data(fpath, Patient_Data)
    patient_df = patient_clean(patient_df, HF, SRP, ERP)
    return patient_df


def send_database(Base_table, Base_data, RRF_An_table, RRF_An_data, NPPL_table, NPPL_data, Patient_table, Patient_data, engine):
    try:
        Base_data.to_sql(Base_table, engine, if_exists='append', index=False)
        RRF_An_data.to_sql(RRF_An_table, engine, if_exists='append', index=False)
        NPPL_data.to_sql(NPPL_table, engine, if_exists='append', index=False)
        if Patient_table != None:
            Patient_data.to_sql(Patient_table, engine, if_exists='append', index=False)
        st.success("All data has successfully loaded to the database.")
    except:
        st.error("Unable to send the data to database!")


def connect_db():
    st.session_state.connect_db = True

def show_clicked():
    st.session_state.show_clicked = True

def upload_clicked():
    st.session_state.upload_clicked = True

def analysis_clicked():
    st.session_state.analysis_clicked = True

def nppl_clicked():
    st.session_state.nppl_clicked = True

def patient_clicked():
    st.session_state.patient_clicked = True

def end_clicked():
    st.session_state.end_clicked = True

def merge_clicked():
    st.session_state.merge_clicked = True


def call_patient_data(fpath, Patient_Data, NPPL, RRF_Analysis, HF, SRP, ERP, engine, track):  
    st.success("Working on NPPL table...")
    nppl_df = nppl_table(fpath, NPPL, HF, SRP, ERP)
                              
    if Patient_Data != None:
        # Display Patient button
        if not st.session_state.patient_clicked:
            st.button("Continue to Patient Table", on_click=patient_clicked)

        if st.session_state.patient_clicked:
            st.success("Working on patient table...")
            patient_df = patient_table(fpath, Patient_Data, HF, SRP, ERP)

            # Display End button
            if not st.session_state.end_clicked:
                st.button("Send to Database", on_click=end_clicked)

            if st.session_state.end_clicked:
                send_database('Track', track, 'RRF_Analysis', RRF_Analysis, 'NPPL', nppl_df, 'Patient', patient_df, engine)
    else:
        st.warning("There is no patient data.")

        # Display End button
        if not st.session_state.end_clicked:
            st.button("Send to Database", on_click=end_clicked)

        if st.session_state.end_clicked:
            send_database('Track', track, 'RRF_Analysis', RRF_Analysis, 'NPPL', nppl_df, None, None, engine)


def reset_app():
    input_container = st.empty()
    st.session_state.show_clicked = False
    st.session_state.upload_clicked = False
    st.session_state.analysis_clicked = False
    st.session_state.nppl_clicked = False
    st.session_state.patient_clicked = False
    st.session_state.end_clicked = False
    st.session_state.merge_clicked = False
    st.session_state.previous_file = None


def main():
    # Initialize session state variables
    if 'connect_db' not in st.session_state:
        st.session_state.connect_db = False
    if 'show_clicked' not in st.session_state:
        st.session_state.show_clicked = False
    if 'upload_clicked' not in st.session_state:
        st.session_state.upload_clicked = False
    if 'analysis_clicked' not in st.session_state:
        st.session_state.analysis_clicked = False
    if 'nppl_clicked' not in st.session_state:
        st.session_state.nppl_clicked = False
    if 'patient_clicked' not in st.session_state:
        st.session_state.patient_clicked = False
    if 'end_clicked' not in st.session_state:
        st.session_state.end_clicked = False
    if 'merge_clicked' not in st.session_state:
        st.session_state.merge_clicked = False
    if 'previous_file' not in st.session_state:
        st.session_state.previous_file = None

    # Display Connect button
    if not st.session_state.connect_db:
        st.button("Connnect", on_click=connect_db)

    if st.session_state.connect_db:
        try:
            engine_url = f"postgresql+psycopg2://postgres:{db_password}@{db_host}/{database_name}"
            engine = create_engine(engine_url)
            with engine.connect():
                show_input = False
                input_container.empty()
                st.success("Successfully connected with the Database.", icon="✅")

            # Display Analysis button
            if not st.session_state.show_clicked:
                st.button("Show Me Files I have Inserted", on_click=show_clicked)

            if st.session_state.show_clicked:
                tracking = pd.read_sql_query('SELECT * FROM public."Track"', engine)
                st.write(tracking)

            fpath = st.file_uploader("Upload a Excel file", type=["xlsx"])

            if fpath is not None and fpath != st.session_state.previous_file:
                reset_app()
                st.session_state.previous_file = fpath

            if fpath is not None:
                if not st.session_state.upload_clicked:
                    st.button("Upload", on_click=upload_clicked)

                if st.session_state.upload_clicked:
                    track, DFF, NPPL, Analysis, Patient_Data, HF, SRP, ERP, data_exists = setup(new_columns, columns_to_drop, int_columns, fpath, engine)

                    # Display Analysis button
                    if not st.session_state.analysis_clicked and not data_exists:
                        st.button("Continue to Analysis Table", on_click=analysis_clicked)

                    if st.session_state.analysis_clicked:
                        st.success("Working on analysis table...")
                        analysis_clean = analysis_table(fpath, Analysis)

                        if len(DFF) > len(analysis_clean):
                            warn = 'There is more drug in RRF Report (' + str(len(DFF)) + ') than Analysis (' + str(len(analysis_clean)) + ')!'
                            st.warning(warn, icon="⚠️")
                            # Display Merge button
                            if not st.session_state.merge_clicked:
                                st.button("Its Okay Merge & Continue to NPPL Table", on_click=merge_clicked)

                            if st.session_state.merge_clicked:
                                RRF_Analysis = merge_rrf(DFF, analysis_clean)
                                call_patient_data(fpath, Patient_Data, NPPL, RRF_Analysis, HF, SRP, ERP, engine, track)

                        elif len(DFF) < len(analysis_clean):
                            warn = 'There is more drug in Analysis (' + str(len(analysis_clean)) + ') than RRF (' + str(len(DFF)) + ')!'
                            st.warning(warn, icon="⚠️")
                            # Display Merge button
                            if not st.session_state.merge_clicked:
                                st.button("Its Okay Merge & Continue to NPPL Table", on_click=merge_clicked)

                            if st.session_state.merge_clicked:
                                RRF_Analysis = merge_rrf(DFF, analysis_clean)
                                call_patient_data(fpath, Patient_Data, NPPL, RRF_Analysis, HF, SRP, ERP, engine, track)
                        else:
                            RRF_Analysis = merge_rrf(DFF, analysis_clean)
                            # Display NPPL button
                            if not st.session_state.nppl_clicked:
                                st.button("Continue to NPPL Table", on_click=nppl_clicked)

                            if st.session_state.nppl_clicked:
                                call_patient_data(fpath, Patient_Data, NPPL, RRF_Analysis, HF, SRP, ERP, engine, track)
        except:
            st.error("Incorrect password or Unable to connect with the database!", icon="❌")
    

if __name__ == "__main__":
    main()
