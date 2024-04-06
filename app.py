import json

from bertopic import BERTopic
from flask import Flask, request, render_template, redirect, url_for, g
import os

from GutenbergPreprocessor import GutenbergPreprocessor


app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def upload_form():
    return render_template('upload.html')


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file:
            # Read and preprocess the file
            content = file.read().decode('utf-8')  # Assuming text content
            processed_content = GutenbergPreprocessor(content)  # Your preprocessing function here

            # Store for use in the same request context
            g.processed_content = processed_content

            # Redirect to the analysis results page
            return redirect(url_for('analyze_book'))

    # If not POST, or if redirection from POST, load upload page
    return render_template('upload.html')


@app.route('/analyze')
def analyze_book():
    if not hasattr(g, 'processed_content'):
        return "No file has been uploaded and processed.", 400

    model_path = "res/unified_bertopic_model.pkl"

    processed_content = [g.processed_content]  # BERTopic expects a list of documents


    # Load document names and topic assignments
    with open("res/document_names.json", 'r', encoding='utf-8') as f:
        document_names = json.load(f)
    with open("res/topic_assignments.json", 'r', encoding='utf-8') as f:
        saved_topics = json.load(f)

    topic_model = BERTopic.load(model_path)

    new_book_texts = []
    for filename in sorted(os.listdir(processed_content)):
        if filename.endswith(".txt"):
            with open(os.path.join(processed_content, filename), 'r', encoding='utf-8') as file:
                chunk_text = file.read()
            new_book_texts.append(chunk_text)

    new_book_topics = topic_model.transform(new_book_texts)
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
