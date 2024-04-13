import fitz
import os
import json


class doc_processor:
    assets_folder_path = ''
    
    def __init__(self, _assets_folder_path, _reformat_folder_path):
        self.assets_folder_path = _assets_folder_path
        self.reformat_folder_path = _reformat_folder_path
    
    def load_file(self, fileName: str) -> fitz.Document:
        # open the pdf file to be read
        doc = fitz.open(self.assets_folder_path+fileName) 
        page_num = len(doc)
        return doc, page_num

    
    def replace_tables(self, fileName: str, pages: list[fitz.Page], page_num: int) -> str:
        '''
        read the pdf file into buffer, detect and replace the tables with JSON, release buffer and return string 
        output format (given m as number of rows, n as number of columns, <column number> and <row number> are 1-base index for users' reference): 
       
        [
            {
                "column <column number> <column name 0> of row <row number> <row name 0>": "text extracted from <0, 0>",
                "column <column number> <column name 0> of row <row number> <row name 1>": "text extracted from <0, 1>",
                ...
                "column <column number> <column name 0> of row <row number> <row name n-1>": "text extracted from <0, n-1>",
            }, ...  
    
        
            {
                "column <column number> <column name j> of row <row number> <row name i>": "text extracted from <i, j>"
            }, ...  

            {
                ...
                "column <column number> <column name n-1> of row <row number> <row name m-1>": "text extracted from <m-1, n-1>"
            } 
        ]
        
        '''
        
        reformat_pages = []

        # last row name is the name of the last row of latest table, which will be applied to the first empty row name of the current table 
        # last_row_name = ''
        for p_n in range(page_num):
          
            page = pages[p_n]
            tables = page.find_tables()
            #tables = page.find_tables(horizontal_strategy="text")
            table_num = len(tables.tables)
            
            # locate the bbox is the bounding box of the table as a tuple (x0, y0, x1, y1).
            # this bbox will be replaced by page.insert_textbox() after the processing of table data is finished 
            reformat_tables = [] # the reformatted tables in the current page
            bbox_list = [table.bbox for table in tables.tables]

            
            for table in tables.tables:
                reformat_table=[]
                # get the number of rows and extract the contents of rows as list[list[str]]
                row_num = table.row_count
                rows = table.extract()
            
                # get the headers (column names)
                headers = table.header.names 
                col_num = len(headers)
                for i in range(row_num):
                    # get the row names (treat the first element of each row as row name)
                    row = rows[i]
                    row_name = ''
                    if row[0] != None:
                        row_name = row[0]
                    row_text = {}
                    for j in range(col_num):
                        col_name = ''
                        if headers[j] != None:
                            col_name = headers[j]

                        row_text["column {:0} '{:1}' of row {:2} '{:3}'".format((j+1), col_name, (i+1), row_name)] = row[j]

                

                    reformat_table.append(row_text)
                reformat_tables.append(reformat_table)
            
            #with open("{}.json".format(self.reformat_folder_path+fileName), 'w') as reformat_log:
            #        json.dump(reformat_tables, reformat_log,indent = 4)
            page.clean_contents()
            for t_n in range(table_num):
                page.add_redact_annot(quad = bbox_list[t_n])
            page.apply_redactions()
            for t_n in range (table_num):
                page.insert_textbox(rect = bbox_list[t_n], fontsize = 3, buffer = str(reformat_tables[t_n]) )

            print("Page {0}: {1}".format(page, page.get_text().encode("UTF-8").decode('UTF-8')))
            reformat_pages.append({str(page): page.get_text(sort=True).encode("UTF-8").decode('UTF-8')})
        with open("{}.json".format(self.reformat_folder_path+fileName), 'w') as reformat_log:
            json.dump(reformat_pages, reformat_log,indent = 4)

        return pages
        
                

    def replace_equations(self, fileName: str, pages: list[fitz.Page], page_num: int):
        '''
        read the pdf file into buffer, detect the character set of equations, release buffer and return string 
        '''

        
        texts = pages[7].get_text(sort=True).encode("UTF-8")


        print(texts.decode('UTF-8'))
        
   
            


if __name__ == '__main__':
    cur_dir = os.path.dirname(__file__)
    dl = doc_processor(_assets_folder_path= '{}/test/assets/'.format(cur_dir),\
                    _reformat_folder_path = '{}/test/reformat/'.format(cur_dir))
    
    _filename = 'Table Test.pdf'

    doc, page_num = dl.load_file(fileName=_filename)
    
    dl.replace_tables(fileName=_filename, pages=doc, page_num=page_num)
    
    with open('{:0}/test/reformat/(reformatted){:1}'.format(cur_dir, _filename), 'w') as rf:
        doc.save(rf)
    #dl.replace_equations(fileName=_filename, pages=doc, page_num=page_num)
    