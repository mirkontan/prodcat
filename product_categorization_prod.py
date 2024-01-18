import streamlit as st
import pandas as pd
import numpy as np
import base64
import io
import datetime
from collections import Counter
from product_cat import *
# Import all lists from the discarded_items module
from under_armour_discarded_items import *
from smeg_discarded_items import *
from not_defined_discarded_items import *


# Define the Streamlit app
st.title('Categorizza Prodotti / Aggiorna lista delle Discarded')

# Define the function to process the uploaded Excel files
def process_files(uploaded_files, product_cat_smeg_dict):
    merged_dfs = []
    checkbox_counter = 0

    for file in uploaded_files:
        df = pd.read_excel(file)
        merged_df = df.copy()

        if 'ITEM_ID' in merged_df.columns:
            pass
        else:
            merged_df['ITEM_ID'] = df['Item ID']

        # merged_df['TITLE'] = df['TITLE'] 
        
        # if 'IMAGE_URL' in df.columns:
        #     pass
        # else:
        #     merged_df['IMAGE_URL'] = df['Image Url']

        # if 'PRODUCT_CATEGORY' in df.columns:
        #     pass
        # else:
        #     merged_df['PRODUCT_CATEGORY'] = df['Product Category']
        

        def map_category(title):
            title = title.lower()  # Convert the title to lowercase for case-insensitive comparison
            for keyword, category in product_cat_dict.items():
                if keyword in title:
                    return category
            return '-'
        
        merged_df['PRODUCT_CATEGORY_SUGGESTED'] = merged_df['TITLE'].apply(map_category)
        merged_dfs.append(merged_df)


        # GESTIONE ECCEZIONI
        # Function to check if both terms are present in the TITLE
        if selected_brand == 'smeg':

            def has_breakfast_kit(title):
                return ('水壶' in title and '多士炉' in title) or ('水壶' in title and '吐司' in title)
           
           
            def latter_has_ecf(title):
                # Get the last 10 characters of the title
                last_title = title[-15:]
                return 'ECF' in last_title
                

            def latter_has_smf(title):
                # Get the last 10 characters of the title
                last_title = title[-15:]
                return 'SMF' in last_title


            def latter_has_klf(title):
                # Get the last 10 characters of the title
                last_title = title[-15:]
                return ('KLF' in last_title) or ('K-LF' in last_title)


            # Update the 'PRODUCT_CATEGORY_SUGGESTED' column based on the condition
            merged_df['PRODUCT_CATEGORY_SUGGESTED'] = merged_df.apply(
                lambda row: 'Breakfast Kit' if has_breakfast_kit(row['TITLE']) else row['PRODUCT_CATEGORY_SUGGESTED'],
                axis=1)
            # Update the 'PRODUCT_CATEGORY_SUGGESTED' column based on the condition
            merged_df['PRODUCT_CATEGORY_SUGGESTED'] = merged_df.apply(
                lambda row: 'Coffee Machine' if latter_has_ecf(row['TITLE']) else row['PRODUCT_CATEGORY_SUGGESTED'],
                axis=1)            # Update the 'PRODUCT_CATEGORY_SUGGESTED' column based on the condition
            merged_df['PRODUCT_CATEGORY_SUGGESTED'] = merged_df.apply(
                lambda row: 'Stand Mixer' if latter_has_smf(row['TITLE']) else row['PRODUCT_CATEGORY_SUGGESTED'],
                axis=1)            

            merged_df['PRODUCT_CATEGORY_SUGGESTED'] = merged_df.apply(
                lambda row: 'Kettle' if latter_has_klf(row['TITLE']) else row['PRODUCT_CATEGORY_SUGGESTED'],
                axis=1)       
            
        # Count the number of rows with '-' in PRODUCT_CATEGORY_SUGGESTED
        no_categorization_count = (merged_df['PRODUCT_CATEGORY_SUGGESTED'] == '-').sum()
        # Total number of rows in the DataFrame
        total_rows = len(merged_df)
        # Display the message
        st.sidebar.write(f"{no_categorization_count} out of {total_rows} products have no categorization.")

        #------------------------------------------------------------------------------------
        #                                       WORDS CLOUD
        #------------------------------------------------------------------------------------


        # Filter rows with '-' in 'PRODUCT_CATEGORY_SUGGESTED'
        filtered_df = merged_df[merged_df['PRODUCT_CATEGORY_SUGGESTED'].str.contains('-')]
        # Extract the "TITLE" column from the filtered DataFrame
        title_column = filtered_df["TITLE"]
        # Combine all titles into a single string
        all_titles = " ".join(title_column)
        # Tokenize the text (using simple whitespace-based tokenization)
        words = all_titles.split()
        # Define the desired n-gram size (e.g., bigrams)
        # Create a selectbox to allow users to choose a number
        n = st.sidebar.selectbox('Selezione n. di parole che dovranno comporre le unità di conteggio:', [1, 2, 3])
        # Generate n-grams
        ngrams = [tuple(words[i:i + n]) for i in range(len(words) - n + 1)]

        # Count the occurrences of each n-gram
        ngram_counts = Counter(ngrams)

        # Sort the n-grams by occurrence in descending order
        sorted_ngram_counts = sorted(ngram_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Generate a unique key for each checkbox
        checkbox_key = f"checkbox_{checkbox_counter}"
        show_word_pairs = st.sidebar.checkbox(f'Show most common Word Pairs within {file.name}', key=checkbox_key)
        # Increment the counter for the next checkbox
        checkbox_counter += 1

        if show_word_pairs:
            st.sidebar.write('Words Pairs most commonly used in TITLE of uncategorized listings')

            # Display the most common n-grams and their counts
            for ngram, count in sorted_ngram_counts:
                if all(len(word) >= 2 for word in ngram):  # Filter out n-grams with single-character words
                    st.sidebar.write(f"{' '.join(ngram)}: {count}")

        #------------------------------------------------------------------------------------
        #                    
        #------------------------------------------------------------------------------------



    return merged_dfs

# Create a list of brands along with their names
brand_list = [
    {'name': 'not_defined', 'list': not_defined},
    {'name': 'smeg', 'list': smeg},
    {'name': 'under_armour', 'list': under_armour}

]
# Create a list of names for the selectbox
list_names = [item['name'] for item in brand_list]
list_names_upper = [item['name'].upper() for item in brand_list]
# Create a Streamlit selectbox for selecting the discarded list
selected_brand_upper = st.sidebar.selectbox("Select the BRAND to analyze:", list_names_upper)
selected_brand = selected_brand_upper.lower()

#-------------------------------------------------------------------------------------------------------------
#                    DISCARDED LISTINGS UPDATE SECTION
#-------------------------------------------------------------------------------------------------------------

discard_listings = st.sidebar.checkbox(f"Discard Listings for: {selected_brand_upper}")
if discard_listings:
        
    # Create a function to append 'ITEM_ID' values to the selected discarded list and save to file
    def append_to_discarded_list(uploaded_file, selected_brand):
        if uploaded_file is not None:
            df = pd.read_excel(uploaded_file)
            if 'ITEM_ID' in df.columns:
                new_discarded_items = df['ITEM_ID'].tolist()

                # Find the selected list by its name
                selected_list = next(item['list'] for item in brand_list if item['name'] == selected_brand)

                # Filter out duplicate 'ITEM_ID' values
                new_discarded_items = [item for item in new_discarded_items if item not in selected_list]

                if new_discarded_items:
                    selected_list.extend(new_discarded_items)
                    st.sidebar.write(f"Discarded 'ITEM_ID' values added to {selected_brand}:")
                    # Create a filename based on the selected name
                    filename = f'/Users/mirkofontana/Desktop/Script_Python/StreamlitApps/PRODUCT_CATEGORIZATION/{selected_brand}_discarded_items.py'
                    # Save the updated list to the corresponding file
                    with open(filename, 'w') as f:
                        f.write(f'{selected_brand} = {selected_list}')
                else:
                    st.write(f"No new 'ITEM_ID' values to append. All provided 'ITEM_ID' values are already in {selected_brand}.")
            else:
                st.write("No 'ITEM_ID' column in the uploaded file.")
        else:
            st.write("No file uploaded. Nothing to append.")

    # Create a file uploader for the selected discarded list
    discarded_listings_file = st.sidebar.file_uploader(f"Upload {selected_brand} listings XLSX file", type=["xlsx"])

    # Check if a discarded list is selected and a file is uploaded
    if discarded_listings_file is not None and selected_brand is not None:
        # Append new 'ITEM_ID' values to the selected discarded list
        append_to_discarded_list(discarded_listings_file, selected_brand)
    # Add a checkbox to control whether to display the discarded list
    show_discarded_list = st.sidebar.checkbox(f"Show discarded list for: {selected_brand_upper}")

    # Check if a discarded list is selected and a file is uploaded
    if discarded_listings_file is not None and selected_brand is not None:
        # Append new 'ITEM_ID' values to the selected discarded list
        append_to_discarded_list(discarded_listings_file, selected_brand)

    # Display the selected discarded list if needed
    if show_discarded_list and selected_brand is not None:
        st.sidebar.write(f"{selected_brand} Discarded 'ITEM_ID' Values:")
        st.sidebar.write(next(item['list'] for item in brand_list if item['name'] == selected_brand))

#-------------------------------------------------------------------------------------------------------------
#                    
#-------------------------------------------------------------------------------------------------------------


uploaded_files = st.file_uploader("Upload one or multiple XLSX files to ", type=["xlsx"], accept_multiple_files=True)

# Initialize a counter to create unique keys

if selected_brand == 'smeg':
    product_cat_dict = product_cat_smeg_dict
    discarded_items_list = smeg

elif selected_brand == 'under_armour':
    product_cat_dict = product_cat_ua_dict
    discarded_items_list = under_armour

elif selected_brand == 'not_defined':
    product_cat_dict = product_cat_overall_dict
    discarded_items_list = not_defined


if uploaded_files:
    merged_dfs = process_files(uploaded_files, product_cat_dict)

    # Check if 'ITEM_ID' in each DataFrame in merged_dfs matches with discarded items
    for df in merged_dfs:
        df['CHECK_DISCARDED'] = df['ITEM_ID'].apply(lambda item_id: 'LISTING DISCARDED' if item_id in discarded_items_list else '-')

    st.write("Merged DataFrame with Suggested Categories:")

    for idx, df in enumerate(merged_dfs):
        st.write(f"DataSource {idx + 1}:")
        st.write(df)


    # Search box for filtering by 'TITLE'
    search_term = st.text_input("Search by TITLE", "")

    # Filter the DataFrame based on the search term
    if search_term:
        for idx, df in enumerate(merged_dfs):
            df_filtered = df[df['TITLE'].str.contains(search_term, case=False)]
            st.write(f"Filtered DataFrame {idx + 1}:")
            st.write(df_filtered)

    # Search box for filtering by 'ITEM_ID'
    search_term2 = st.text_input("Search by ITEM_ID", "")
    # Filter the DataFrame based on the search term
    if search_term2:
        for idx, df in enumerate(merged_dfs):
            df_filtered = df[df['ITEM_ID'].str.contains(search_term2, case=False)]
            st.write(f"Filtered DataFrame {idx + 1}:")
            st.write(df_filtered)

    # Download the data as XLSX
    for idx, df in enumerate(merged_dfs):
        uploaded_filename = uploaded_files[idx].name
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name=f'Listings_categorized{idx + 1}', index=False)
        b64 = base64.b64encode(output.getvalue()).decode()
        st.markdown(f"Download {uploaded_filename} as XLSX: [{uploaded_filename}](data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64})", unsafe_allow_html=True)

# Run the Streamlit app
if __name__ == '__main__':
    st.write('Upload one or multiple XLSX files to begin.')
