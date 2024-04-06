import json

from bertopic import BERTopic
from flask import Flask, request, render_template, redirect, url_for, g
import os

from GutenbergPreprocessor import GutenbergPreprocessor

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CLEANED_FOLDER'] = 'cleaned_files'


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)

            preprocessor = GutenbergPreprocessor(filepath)
            cleaned_path = preprocessor.process_file()
            cleaned_filename = os.path.basename(cleaned_path)

            return redirect(url_for('analyze_book', filename=cleaned_filename))
    return render_template('upload.html')

@app.route('/analyze')
def analyze_book():
    filename = request.args.get('filename')
    if not filename:
        return "No file has been specified for analysis.", 400


    cleaned_path = os.path.join(app.config['CLEANED_FOLDER'], filename)
    if not os.path.exists(cleaned_path):
        return "The specified file does not exist.", 404

    # # Load the cleaned file content
    # with open(cleaned_path, 'r', encoding='utf-8') as file:
    #     processed_content = file.read()

    model_path = "res/unified_bertopic_model.pkl"

    # Load document names and topic assignments
    with open("res/document_names.json", 'r', encoding='utf-8') as f:
        document_names = json.load(f)
    with open("res/topic_assignments.json", 'r', encoding='utf-8') as f:
        saved_topics = json.load(f)

    topic_model = BERTopic.load(model_path)


    # Read the processed content from the cleaned file
    with open(g.cleaned_path, 'r', encoding='utf-8') as file:
        processed_content = [file.read()]  # Note: [file.read()] makes it a list, as expected by BERTopic

    new_book_topics = topic_model.transform(processed_content)
    assigned_topics, probabilities = new_book_topics

    unique_topics = set(assigned_topics)
    if -1 in unique_topics:
        unique_topics.remove(-1)

    topics_words = {}
    for topic in unique_topics:
        topic_words = topic_model.get_topic(topic)
        topic_words_list = [word[0] for word in topic_words]
        topics_words[topic] = ', '.join(topic_words_list)

    documents_for_topics = {}
    for topic in unique_topics:
        doc_indices = [i for i, t in enumerate(saved_topics) if t == topic]
        documents_for_topics[topic] = [document_names[idx] for idx in doc_indices]

    return render_template('analyze_results.html', topics_words=topics_words, documents_for_topics=documents_for_topics)


if __name__ == '__main__':
    # Create upload folder if it doesn't exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
