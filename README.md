
# MedicalPlab: Medical Question Bank & API

This project lets you extract, store, and retrieve medical exam questions from PDF files, and provides a web interface for easy access. You do **not** need to know Python to use it—just follow the steps below.

---

## 📁 Project Structure

```
MedicalPlab/
├── main.py                  # The backend server (API)
├── streamlit_app.py         # The web interface (easy to use)
├── Scripts/                 # Helper scripts for extracting and processing questions
│   ├── extract_plabable.py
│   ├── RetrieveQuestionsFromPlabable.py
│   ├── RetrieveQuestionsFromUni.py
│   └── utils.py
├── Data/                    # Where your PDFs and database live
│   └── db/                  # The SQLite database (auto-created)
│   └── Plabable/Topics/     # Your source PDFs
├── README.md                # This file
├── pyproject.toml           # Project dependencies (for setup)
└── .gitignore
```

---

## 🚀 How to Run Everything (No Python Knowledge Needed)

### 1. Install Python
If you don't have Python, download it from [python.org](https://www.python.org/downloads/) and install it. (Choose version 3.10 or newer.)

### 2. Open a Terminal (Command Prompt)
On Windows: Press `Win + R`, type `cmd`, and hit Enter.
On Mac: Open `Terminal` from Applications.
On Linux: Open your terminal app.

### 3. Go to the Project Folder
Type `cd` followed by the path to this project. Example:
```
cd path/to/MedicalPlab
```

### 4. Install All Requirements
Copy and paste this command:
```
pip install -r requirements.txt
```
If you don't have a `requirements.txt`, use:
```
pip install fastapi uvicorn streamlit pdfplumber
```

### 5. Start the Backend (API)
Copy and paste:
```
uvicorn main:app --reload
```
Leave this window open.

### 6. Start the Web Interface
Open a **new** terminal window, go to the project folder again, and run:
```
streamlit run streamlit_app.py
```

### 7. Use the App
Your browser will open automatically. If not, go to [http://localhost:8501](http://localhost:8501) in your browser.

You can now:
- Choose the question source (Plabable or Uni)
- Enter how many questions you want
- (Optionally) enter a topic or level
- Click to get your questions!

---

## 🛠️ What Each File/Folder Does

- **main.py**: The backend server. Handles requests for questions.
- **streamlit_app.py**: The web interface. Lets you use the app in your browser.
- **Scripts/**: Helper scripts for extracting and processing questions from PDFs.
- **Data/**: Where your PDFs and the database are stored.
- **pyproject.toml**: Lists the required Python packages.

---

## ❓ FAQ

**Q: I get an error about missing packages?**  
A: Run the install command in step 4 again.

**Q: How do I add new PDFs?**  
A: Put them in `Data/Plabable/Topics/` and re-run the extraction script if needed.

**Q: How do I stop the app?**  
A: Press `Ctrl+C` in the terminal windows.

---

## 👩‍💻 Need Help?
If you get stuck, please reach out to any of the project developers.
