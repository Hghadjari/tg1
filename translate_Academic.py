#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 12 09:52:06 2024

@author: hossein
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  5 10:10:27 2024

@author: hosseinghadjari
"""
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov  3 18:16:07 2024

@author: hosseinghadjari
"""

import re
import os
import time
import shutil
import PyPDF2
import google.generativeai as genai

# Configure the Google Gemini API
GEMINI_API_KEY = "AIzaSyDwQ8u16-vOWkDGFUFSq7efpCK3IciW1EA"
genai.configure(api_key=GEMINI_API_KEY)

# Create the model
model = genai.GenerativeModel("gemini-1.5-flash")

# Helper function for natural sorting based on numbers in filenames
def natural_sort_key(filename):
    numbers = re.findall(r'\d+', filename)
    return int(numbers[0]) if numbers else float('inf')

# Function to clean a folder (delete all its contents)
def clean_folder(folder_path):
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)  # Delete the folder and its contents
        print(f"Cleaned folder: {folder_path}")
    os.makedirs(folder_path)  # Recreate the empty folder

# Function to extract text from specific pages of a PDF file
def extract_text_from_pdf(pdf_path, start_page, end_page):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        pdf_text = ""
        for page_num in range(start_page - 1, end_page):
            pdf_text += reader.pages[page_num].extract_text() + "\n\n"
    return pdf_text

# Function to clean up text by removing specific patterns and excessive blank lines
def clean_text(text):
    patterns = [r'\|\s*THE LONELIEST REVOLUTION', r'introduction\s*\|', r'^\d+\s*$', r'\n{5,}']
    text = re.sub('|'.join(patterns), '', text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r'\n{2,}', '\n', text)
    return text

# Split text into batched paragraphs
def split_into_paragraphs(text, max_paragraphs=8):
    paragraphs = [para.strip() for para in re.split(r'(?<=\.)\n+', text) if para.strip()]
    batched_paragraphs = ['\n\n'.join(paragraphs[i:i + max_paragraphs]) for i in range(0, len(paragraphs), max_paragraphs)]
    return batched_paragraphs

# Function for saving text to a combined output file
def save_combined_output(text, combined_file_path):
    with open(combined_file_path, 'a', encoding='utf-8') as file:
        file.write(text + "\n\n")

# First Layer Translation and Save Output
# First Layer Translation and Save Output with Enhanced Error Handling
def translate_paragraph(batch, output_folder, batch_num):
    prompt = f"""
Translate the following text into formal, clear, and accessible Farsi, specifically for a public audience in Iran interested in history or political science. Follow these guidelines:
0. Please don't use any symol or number or language other than farsi language. It make to format file diffcult to read'
00. Translate or transliterate all English names or words into Farsi script. If direct translation is not appropriate (e.g., names), provide a Farsi-friendly equivalent to ensure smooth reading.

1. **Maintain Clarity and Precision**: Translate with a focus on clear communication of historical or political concepts without unnecessary complexity. Avoid overly poetic or literary language.
2. **Focus on Meaning Over Literal Translation**: Capture the intent of the source text, using phrasing that is natural in Farsi and suits an educated, non-specialist audience.
3. **Preserve Academic Tone**: Use formal language appropriate for an academic text, maintaining the seriousness and formality of historical or political content.
4. **Historical and Political Vocabulary**: Ensure that all specialized terms are correctly translated to reflect their specific meaning . Use consistent terminology throughout the translation.
5. **Avoid Literary Embellishment**: Keep the language straightforward, avoiding metaphors or flowery expressions unless they are present in the original text and essential to the meaning. Grammar and Style: Maintain proper grammar and style in the Farsi translation. Use natural and idiomatic language while preserving the tone and style of the original text.
6. Religious Nuances:  Religious terms and concepts require careful translation to ensure their proper understanding in the Farsi context, particularly considering the different religious landscape in Iran. 
Translate the following text into formal, clear, and accessible Farsi, specifically for a public audience in Iran interested in history or political science
Text: {batch}

Please output only the Farsi translation, with no additional comments.
"""

    try:
        response = model.generate_content(
            prompt,
            generation_config={'temperature': 0.95},
            safety_settings={
                'HATE': 'BLOCK_NONE',
                'HARASSMENT': 'BLOCK_NONE',
                'SEXUAL': 'BLOCK_NONE',
                'DANGEROUS': 'BLOCK_NONE'
            }
        )
        if response and response.text:
            translated_text = response.text.strip()
        else:
            # Log untranslatable batch
            translated_text = "[Untranslatable batch]"
            print(f"Warning: Batch {batch_num} could not be translated. Logging for later review.")
            with open(os.path.join(output_folder, "untranslatable_batches.txt"), 'a', encoding='utf-8') as log_file:
                log_file.write(f"Batch {batch_num} was untranslatable:\n{batch}\n\n")

    except Exception as e:
        # Handle unexpected errors gracefully and log the batch
        translated_text = f"[Error: {str(e)}]"
        print(f"An error occurred while processing batch {batch_num}: {e}")
        with open(os.path.join(output_folder, "untranslatable_batches.txt"), 'a', encoding='utf-8') as log_file:
            log_file.write(f"Batch {batch_num} encountered an error: {str(e)}\nContent:\n{batch}\n\n")

    # Save the first layer output
    file_path = os.path.join(output_folder, f"batch_{batch_num}_first_layer.txt")
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(translated_text)

    save_combined_output(translated_text, os.path.join(output_folder, "combined_first_layer.txt"))
    return translated_text


# Second Layer Refinement and Save Output with Enhanced Error Handling
def refine_translation(batch, translation, output_folder, batch_num):
    prompt = f"""
Refine the following Farsi translation to ensure it flows smoothly and reads naturally, while maintaining clarity and formal readability,Identify and correct any sentences that sound awkward or unnatural in Farsi, even if they are technically accurate translations. Making sure it is easy for a public audience to understand historical or political science concepts. Follow these guidelines:
0. Please don't use any symol or number or language other than farsi language. It make to format file diffcult to read'
00.0. Translate or transliterate all English names or words into Farsi script. If direct translation is not appropriate (e.g., names), provide a Farsi-friendly equivalent to ensure smooth reading.

1. **Ensure Smooth Flow and Coherence**: Polish sentences to improve clarity and coherence, enhancing readability without adding poetic elements.
2. **Use Academic Vocabulary Thoughtfully**: Replace any vague terms with precise, appropriate historical or political terminology.
3. **Maintain Formal Tone**: Ensure the text remains formal and professional, avoiding any casual or overly ornate expressions.
4. **Focus on Accurate Terminology**: Double-check terms related to history and political science to ensure accuracy and appropriateness in the context.
5.Historical Context: The book is about a historic or political issue. Understanding the historical context of the text is essential for accurate translation. Research the historical events and figures mentioned to ensure their proper translation and understanding in Farsi. 
6. Political subtext and implications should be accurately conveyed in the translation. Research the political context and any sensitive political undertones to ensure a nuanced and accurate translation.   
Original English Text: {batch}

Layer 1 Farsi Translation: {translation}

Please output only the improved Farsi translation, without additional comments.
"""

    try:
        response = model.generate_content(
            prompt,
            generation_config={'temperature': 1},
            safety_settings={
                'HATE': 'BLOCK_NONE',
                'HARASSMENT': 'BLOCK_NONE',
                'SEXUAL': 'BLOCK_NONE',
                'DANGEROUS': 'BLOCK_NONE'
            }
        )
        if response and response.text:
            refined_text = response.text.strip()
        else:
            # Log untranslatable batch with its content for later review
            refined_text = "[Untranslatable batch]"
            print(f"Warning: Batch {batch_num} could not be refined. Logging for later review.")
            with open(os.path.join(output_folder, "untranslatable_batches.txt"), 'a', encoding='utf-8') as log_file:
                log_file.write(f"Batch {batch_num} was untranslatable during refinement:\n{batch}\n\n")

    except Exception as e:
        # Handle unexpected errors gracefully and log the batch with an error message
        refined_text = f"[Error: {str(e)}]"
        print(f"An error occurred while refining batch {batch_num}: {e}")
        with open(os.path.join(output_folder, "untranslatable_batches.txt"), 'a', encoding='utf-8') as log_file:
            log_file.write(f"Batch {batch_num} encountered an error during refinement: {str(e)}\nContent:\n{batch}\n\n")

    # Save the second layer output
    file_path = os.path.join(output_folder, f"batch_{batch_num}_second_layer.txt")
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(refined_text)

    save_combined_output(refined_text, os.path.join(output_folder, "combined_second_layer.txt"))
    return refined_text


def elevate_farsi_translation(refined_text, output_folder, batch_num):
    prompt = f"""
Enhance the following Farsi translation, ensuring it maintains a polished, formal tone suitable for an academic audience
while remaining fluent and easy to read. Follow these guidelines:
0. Please don't use any symol or number or language other than farsi language. It make to format file diffcult to read'
00. Translate or transliterate all English names or words into Farsi script. If direct translation is not appropriate (e.g., names), provide a Farsi-friendly equivalent to ensure smooth reading.

1. **Refined Vocabulary**: Replace simpler words with formal, accurate academic terms when appropriate to elevate the tone for historical or political science content.
2. **Avoid Literary Flourishes**: Ensure the language remains direct, focusing on clear and precise communication rather than poetic expressions.
3. **Readability and Accessibility**: Keep the translation accessible, avoiding overly complex structures, while ensuring it flows naturally in Farsi.

Layer 2 Farsi Translation: {refined_text}

Please output only the enhanced Farsi translation, without any additional comments or explanations.
"""

    try:
        response = model.generate_content(prompt, generation_config={'temperature': 0.95}, safety_settings={
                        'HATE': 'BLOCK_NONE',
                        'HARASSMENT': 'BLOCK_NONE',
                        'SEXUAL': 'BLOCK_NONE',
                        'DANGEROUS': 'BLOCK_NONE'
                    })
        
        elevated_text = response.text.strip() if response and response.text else "[Untranslatable batch]"
        if elevated_text == "[Untranslatable batch]":
            print(f"Warning: Batch {batch_num} could not be elevated. Logging for later review.")
            with open(os.path.join(output_folder, "untranslatable_batches.txt"), 'a', encoding='utf-8') as log_file:
                log_file.write(f"Batch {batch_num} was untranslatable during elevation:\n{refined_text}\n\n")

    except Exception as e:
        elevated_text = f"[Error: {str(e)}]"
        print(f"An error occurred while elevating batch {batch_num}: {e}")
        with open(os.path.join(output_folder, "untranslatable_batches.txt"), 'a', encoding='utf-8') as log_file:
            log_file.write(f"Batch {batch_num} encountered an error during elevation: {str(e)}\nContent:\n{refined_text}\n\n")

    # Save the third layer output
    file_path = os.path.join(output_folder, f"batch_{batch_num}_third_layer.txt")
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(elevated_text)

    save_combined_output(elevated_text, os.path.join(output_folder, "combined_third_layer.txt"))
    return elevated_text




# Process each batch through all layers sequentially and save results
def process_batches(pdf_path, start_page, end_page, output_folder_path, start_batch):
    clean_folder(output_folder_path) if start_batch == 1 else None  # Clean only if starting from batch 1
    pdf_text = extract_text_from_pdf(pdf_path, start_page, end_page)
    cleaned_text = clean_text(pdf_text)
    batches = split_into_paragraphs(cleaned_text, max_paragraphs=10)

    combined_final_output = ""

    for i, batch in enumerate(batches, start=1):
        # Skip already processed batches
        if i < start_batch:
            continue

        print(f"Processing batch {i}/{len(batches)}")

        # First Layer: Translation
        translated_text = translate_paragraph(batch, output_folder_path, i)

        # Second Layer: Refinement
        refined_text = refine_translation(batch, translated_text, output_folder_path, i)

        # Third Layer: Elevation
        elevated_text = elevate_farsi_translation(refined_text, output_folder_path, i)

        # Fourth Layer: Final Refinement
        #final_translation = final_refinement(elevated_text, output_folder_path, i)

        # Append the final output of all layers to a combined final output
        combined_final_output += (
            f"Batch {i} Layer 1:\n{translated_text}\n\n"
            f"Batch {i} Layer 2:\n{refined_text}\n\n"
            f"Batch {i} Layer 3:\n{elevated_text}\n\n"
            
        )

        # Optional delay to respect API rate limits
        time.sleep(40)

    # Save concatenated final output of all layers for all batches
    concatenated_final_path = os.path.join(output_folder_path, "final_combined_translation_all_layers.txt")
    with open(concatenated_final_path, 'w', encoding='utf-8') as file:
        file.write(combined_final_output)
    
    print(f"All batches processed and combined in {concatenated_final_path}")

# Example usage
pdf_path = "Lobbying_for_Zionism_on_Both_Sides_of_the_Atlantic_Ilan_Pappe_2024.pdf"
start_page =7
end_page = 531
output_folder_path = os.path.join(os.path.dirname(pdf_path), "translated_batches_Lobbying_for_Zionism_on_Both_Sides_of_the_Atlantic_Ilan_Pappe_2024")

# Set start_batch to resume from batch 1
process_batches(pdf_path, start_page, end_page, output_folder_path, start_batch=1)
