# open source file (pdf, text, json, etx)
# break the file onto n chunks (each chunk 128 token) -> put all of them on a data structure
# loop through the vector and send ony by one to the llm
# collect your results on a new vectore
# merge all results and generate the final translation
# generate the output on pdf or any other format