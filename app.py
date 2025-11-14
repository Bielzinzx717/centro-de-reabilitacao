from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime
import re

app = Flask(__name__)
app.secret_key = 'chave_secreta_reabilitacao_2024'

# Inicializar banco de dados
def init_db():
    conn = sqlite3.connect('reabilitacao.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL,
            telefone TEXT NOT NULL,
            data_entrada TEXT NOT NULL,
            data_saida TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Validar CPF
def validar_cpf(cpf):
    cpf = re.sub(r'\D', '', cpf)
    return len(cpf) == 11

# Validar Email
def validar_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

@app.route('/')
def index():
    conn = sqlite3.connect('reabilitacao.db')
    cursor = conn.cursor()
    
    # Capturar parâmetros de busca e filtros
    busca = request.args.get('busca', '')
    status = request.args.get('status', '')
    data_inicio = request.args.get('data_inicio', '')
    data_fim = request.args.get('data_fim', '')
    
    # Construir query SQL dinamicamente
    query = 'SELECT * FROM clientes WHERE 1=1'
    params = []
    
    # Filtro de busca por nome, CPF ou email
    if busca:
        query += ' AND (nome LIKE ? OR cpf LIKE ? OR email LIKE ?)'
        busca_param = f'%{busca}%'
        params.extend([busca_param, busca_param, busca_param])
    
    # Filtro por status (ativo ou finalizado)
    if status == 'ativo':
        query += ' AND data_saida IS NULL'
    elif status == 'finalizado':
        query += ' AND data_saida IS NOT NULL'
    
    # Filtro por período de entrada
    if data_inicio:
        query += ' AND data_entrada >= ?'
        params.append(data_inicio)
    
    if data_fim:
        query += ' AND data_entrada <= ?'
        params.append(data_fim)
    
    query += ' ORDER BY id DESC'
    
    cursor.execute(query, params)
    clientes = cursor.fetchall()
    
    # Calcular estatísticas
    cursor.execute('SELECT COUNT(*) FROM clientes')
    total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM clientes WHERE data_saida IS NULL')
    ativos = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM clientes WHERE data_saida IS NOT NULL')
    finalizados = cursor.fetchone()[0]
    
    conn.close()
    
    return render_template('index.html', 
                         clientes=clientes, 
                         total=total, 
                         ativos=ativos, 
                         finalizados=finalizados,
                         busca=busca,
                         status=status,
                         data_inicio=data_inicio,
                         data_fim=data_fim)

@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    if request.method == 'POST':
        nome = request.form['nome']
        cpf = request.form['cpf']
        email = request.form['email']
        telefone = request.form['telefone']
        data_entrada = request.form['data_entrada']
        data_saida = request.form['data_saida'] if request.form['data_saida'] else None
        
        # Validações
        if not validar_cpf(cpf):
            flash('CPF inválido! Deve conter 11 dígitos.', 'error')
            return redirect(url_for('cadastrar'))
        
        if not validar_email(email):
            flash('Email inválido!', 'error')
            return redirect(url_for('cadastrar'))
        
        try:
            conn = sqlite3.connect('reabilitacao.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO clientes (nome, cpf, email, telefone, data_entrada, data_saida)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (nome, cpf, email, telefone, data_entrada, data_saida))
            conn.commit()
            conn.close()
            flash('Cliente cadastrado com sucesso!', 'success')
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            flash('CPF já cadastrado no sistema!', 'error')
            return redirect(url_for('cadastrar'))
    
    return render_template('cadastrar.html')

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    conn = sqlite3.connect('reabilitacao.db')
    cursor = conn.cursor()
    
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        telefone = request.form['telefone']
        data_entrada = request.form['data_entrada']
        data_saida = request.form['data_saida'] if request.form['data_saida'] else None
        
        if not validar_email(email):
            flash('Email inválido!', 'error')
            return redirect(url_for('editar', id=id))
        
        cursor.execute('''
            UPDATE clientes 
            SET nome=?, email=?, telefone=?, data_entrada=?, data_saida=?
            WHERE id=?
        ''', (nome, email, telefone, data_entrada, data_saida, id))
        conn.commit()
        conn.close()
        flash('Cliente atualizado com sucesso!', 'success')
        return redirect(url_for('index'))
    
    cursor.execute('SELECT * FROM clientes WHERE id=?', (id,))
    cliente = cursor.fetchone()
    conn.close()
    return render_template('editar.html', cliente=cliente)

@app.route('/deletar/<int:id>')
def deletar(id):
    conn = sqlite3.connect('reabilitacao.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM clientes WHERE id=?', (id,))
    conn.commit()
    conn.close()
    flash('Cliente removido com sucesso!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
