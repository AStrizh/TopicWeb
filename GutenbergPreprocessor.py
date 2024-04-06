import os
import re
import chardet
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

# Ensure necessary NLTK datasets are downloaded
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

class GutenbergPreprocessor:
    def __init__(self, file_path, output_directory='cleaned_files'):
        self.file_path = file_path
        self.output_directory = output_directory
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()

        # Ensure the output directory exists
        os.makedirs(self.output_directory, exist_ok=True)

    def read_and_correct_encoding(self):
        """Detect and correct file encoding to UTF-8."""
        with open(self.file_path, 'rb') as file:
            raw_data = file.read()
            encoding = chardet.detect(raw_data)['encoding']

        with open(self.file_path, encoding=encoding) as file:
            content = file.read()

        return content

    def remove_headers_and_footers(self, content):
        """Remove Gutenberg headers and footers from the content."""
        start_pattern = re.compile(r'\*\*\* START OF (THIS|THE) PROJECT GUTENBERG EBOOK (.+?) \*\*\*', re.IGNORECASE)
        end_pattern = re.compile(r'\*\*\* END OF (THIS|THE) PROJECT GUTENBERG EBOOK', re.IGNORECASE)

        start_match = start_pattern.search(content)
        if start_match:
            content_start_index = start_match.end()
        else:
            content_start_index = 0

        end_match = end_pattern.search(content, content_start_index)
        if end_match:
            content = content[content_start_index:end_match.start()]
        else:
            content = content[content_start_index:]

        return content

    def lemmatize_and_tokenize(self, content):
        """Tokenize and lemmatize the content."""
        tokens = word_tokenize(content)
        lemmatized_tokens = [self.lemmatizer.lemmatize(token) for token in tokens]
        return lemmatized_tokens

    def clean_content(self, tokens):
        """Remove stopwords and unnecessary punctuation from the tokens."""
        cleaned_tokens = [token.lower() for token in tokens if token.isalpha() and token.lower() not in self.stop_words]
        return cleaned_tokens

    def process_file(self):
        """Process the file through all steps and save the cleaned content to a new file."""
        content = self.read_and_correct_encoding()
        content = self.remove_headers_and_footers(content)
        tokens = self.lemmatize_and_tokenize(content)
        cleaned_tokens = self.clean_content(tokens)

        # Generate the output file path
        base_filename = os.path.basename(self.file_path)
        cleaned_filename = 'cleaned_' + base_filename
        cleaned_path = os.path.join(self.output_directory, cleaned_filename)

        # Write the cleaned content to the new file
        with open(cleaned_path, 'w', encoding='utf-8') as cleaned_file:
            cleaned_content = ' '.join(cleaned_tokens)
            cleaned_file.write(cleaned_content)

        return cleaned_path
