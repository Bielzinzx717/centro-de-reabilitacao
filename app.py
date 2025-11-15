from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime
import re
import json
import threading

app = Flask(__name__)
app.secret_key = 'chave_secreta_reabilitacao_2024'

_thread_local = threading.local()

def get_db():
    """Obtém conexão SQLite com configurações otimizadas para evitar locks"""
    if not hasattr(_thread_local, 'db'):
        conn = sqlite3.connect('reabilitacao.db', timeout=30.0, check_same_thread=False)
        conn.execute('PRAGMA journal_mode = WAL')  
        conn.execute('PRAGMA synchronous = NORMAL')
        conn.execute('PRAGMA cache_size = -64000')  
        conn.execute('PRAGMA temp_store = MEMORY')
        conn.row_factory = sqlite3.Row
        _thread_local.db = conn
    return _thread_local.db


def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL,
            telefone TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fichas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            data_entrada TEXT NOT NULL,
            data_saida TEXT,
            observacoes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS medicamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ficha_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
            dosagem TEXT NOT NULL,
            frequencia TEXT NOT NULL,
            observacoes TEXT,
            FOREIGN KEY (ficha_id) REFERENCES fichas(id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()

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
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        
        busca = request.args.get('busca', '')
        status = request.args.get('status', '')
        data_inicio = request.args.get('data_inicio', '')
        data_fim = request.args.get('data_fim', '')
        
        query = '''
            SELECT c.id, c.nome, c.cpf, c.email, c.telefone,
                   f.id as ficha_id, f.data_entrada, f.data_saida, f.created_at
            FROM clientes c
            LEFT JOIN fichas f ON c.id = f.cliente_id
            WHERE 1=1
        '''
        params = []
        
        
        if busca:
            query += ' AND (c.nome LIKE ? OR c.cpf LIKE ? OR c.email LIKE ?)'
            busca_param = f'%{busca}%'
            params.extend([busca_param, busca_param, busca_param])
        
        
        if status == 'ativo':
            query += ' AND f.data_saida IS NULL'
        elif status == 'finalizado':
            query += ' AND f.data_saida IS NOT NULL'
        
        
        if data_inicio:
            query += ' AND f.data_entrada >= ?'
            params.append(data_inicio)
        
        if data_fim:
            query += ' AND f.data_entrada <= ?'
            params.append(data_fim)
        
        query += ' ORDER BY c.id DESC, f.created_at DESC'
        
        cursor.execute(query, params)
        resultados = cursor.fetchall()
        
        clientes_dict = {}
        for row in resultados:
            cliente_id = row[0]
            if cliente_id not in clientes_dict:
                clientes_dict[cliente_id] = {
                    'id': row[0],
                    'nome': row[1],
                    'cpf': row[2],
                    'email': row[3],
                    'telefone': row[4],
                    'fichas': []
                }
            
            if row[5]:  
                clientes_dict[cliente_id]['fichas'].append({
                    'id': row[5],
                    'data_entrada': row[6],
                    'data_saida': row[7],
                    'created_at': row[8]
                })
        
        clientes = list(clientes_dict.values())
        
        # Calcular estatísticas
        cursor.execute('SELECT COUNT(DISTINCT cliente_id) FROM fichas')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM fichas WHERE data_saida IS NULL')
        ativos = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM fichas WHERE data_saida IS NOT NULL')
        finalizados = cursor.fetchone()[0]
        
        return render_template('index.html', 
                             clientes=clientes, 
                             total=total, 
                             ativos=ativos, 
                             finalizados=finalizados,
                             busca=busca,
                             status=status,
                             data_inicio=data_inicio,
                             data_fim=data_fim)
    except Exception as e:
        flash(f'Erro ao carregar página: {str(e)}', 'error')
        return render_template('index.html', clientes=[], total=0, ativos=0, finalizados=0)

@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        cpf = request.form.get('cpf', '').strip()
        email = request.form.get('email', '').strip()
        telefone = request.form.get('telefone', '').strip()
        data_entrada = request.form.get('data_entrada', '').strip()
        data_saida = request.form.get('data_saida', '').strip() or None
        observacoes = request.form.get('observacoes', '').strip()
        
        
        if not nome or not cpf or not email or not telefone or not data_entrada:
            flash('Todos os campos obrigatórios devem ser preenchidos!', 'error')
            return redirect(url_for('cadastrar'))
        
        medicamentos_json = request.form.get('medicamentos_data', '[]')
        try:
            medicamentos = json.loads(medicamentos_json)
        except:
            medicamentos = []
        
        
        if not validar_cpf(cpf):
            flash('CPF inválido! Deve conter 11 dígitos.', 'error')
            return redirect(url_for('cadastrar'))
        
        if not validar_email(email):
            flash('Email inválido!', 'error')
            return redirect(url_for('cadastrar'))
        
        cpf_limpo = re.sub(r'\D', '', cpf)
        
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            cursor.execute('BEGIN IMMEDIATE')
            
            
            try:
                cursor.execute('''
                    INSERT INTO clientes (nome, cpf, email, telefone)
                    VALUES (?, ?, ?, ?)
                ''', (nome, cpf_limpo, email, telefone))
                cliente_id = cursor.lastrowid
                novo_cliente = True
            except sqlite3.IntegrityError:
                cursor.execute('SELECT id FROM clientes WHERE cpf = ?', (cpf_limpo,))
                resultado = cursor.fetchone()
                if resultado:
                    cliente_id = resultado[0]
                    novo_cliente = False
                else:
                    raise
            
            
            cursor.execute('''
                INSERT INTO fichas (cliente_id, data_entrada, data_saida, observacoes)
                VALUES (?, ?, ?, ?)
            ''', (cliente_id, data_entrada, data_saida, observacoes))
            ficha_id = cursor.lastrowid
            
           
            for med in medicamentos:
                if med.get('nome') and med.get('dosagem'):
                    cursor.execute('''
                        INSERT INTO medicamentos (ficha_id, nome, dosagem, frequencia, observacoes)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (ficha_id, med['nome'], med['dosagem'], med.get('frequencia', ''), med.get('observacoes', '')))
            
            conn.commit()
            
            if novo_cliente:
                flash('Novo cliente cadastrado com sucesso!', 'success')
            else:
                flash('Cliente com este CPF já existe no sistema. Nova ficha criada!', 'info')
            
            return redirect(url_for('ver_cliente', cliente_id=cliente_id))
            
        except sqlite3.IntegrityError as e:
            conn.rollback()
            flash('Erro de integridade no banco de dados! Verifique os dados e tente novamente.', 'error')
            return redirect(url_for('cadastrar'))
        except Exception as e:
            conn.rollback()
            flash(f'Erro ao cadastrar: {str(e)}', 'error')
            return redirect(url_for('cadastrar'))
    
    return render_template('cadastrar.html')

@app.route('/nova-ficha/<int:cliente_id>', methods=['GET', 'POST'])
def nova_ficha(cliente_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM clientes WHERE id=?', (cliente_id,))
    cliente = cursor.fetchone()
    
    if not cliente:
        flash('Cliente não encontrado!', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        data_entrada = request.form['data_entrada']
        data_saida = request.form['data_saida'] if request.form['data_saida'] else None
        observacoes = request.form.get('observacoes', '')
        
        medicamentos_json = request.form.get('medicamentos_data', '[]')
        try:
            medicamentos = json.loads(medicamentos_json)
        except:
            medicamentos = []
        
        try:
            cursor.execute('BEGIN IMMEDIATE')
            
            cursor.execute('''
                INSERT INTO fichas (cliente_id, data_entrada, data_saida, observacoes)
                VALUES (?, ?, ?, ?)
            ''', (cliente_id, data_entrada, data_saida, observacoes))
            ficha_id = cursor.lastrowid
            
            for med in medicamentos:
                if med.get('nome') and med.get('dosagem'):
                    cursor.execute('''
                        INSERT INTO medicamentos (ficha_id, nome, dosagem, frequencia, observacoes)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (ficha_id, med['nome'], med['dosagem'], med.get('frequencia', ''), med.get('observacoes', '')))
            
            conn.commit()
            flash('Nova ficha criada com sucesso!', 'success')
            return redirect(url_for('ver_cliente', cliente_id=cliente_id))
        except Exception as e:
            conn.rollback()
            flash(f'Erro ao criar ficha: {str(e)}', 'error')
            return redirect(url_for('nova_ficha', cliente_id=cliente_id))
    
    return render_template('nova_ficha.html', cliente=cliente)

@app.route('/cliente/<int:cliente_id>')
def ver_cliente(cliente_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM clientes WHERE id=?', (cliente_id,))
    cliente = cursor.fetchone()
    
    if not cliente:
        flash('Cliente não encontrado!', 'error')
        return redirect(url_for('index'))
    
    
    cursor.execute('''
        SELECT id, data_entrada, data_saida, observacoes, created_at
        FROM fichas
        WHERE cliente_id = ?
        ORDER BY created_at DESC
    ''', (cliente_id,))
    fichas = cursor.fetchall()
    
    
    fichas_com_medicamentos = []
    for ficha in fichas:
        cursor.execute('''
            SELECT id, nome, dosagem, frequencia, observacoes
            FROM medicamentos
            WHERE ficha_id = ?
        ''', (ficha[0],))
        medicamentos = cursor.fetchall()
        
        fichas_com_medicamentos.append({
            'id': ficha[0],
            'data_entrada': ficha[1],
            'data_saida': ficha[2],
            'observacoes': ficha[3],
            'created_at': ficha[4],
            'medicamentos': medicamentos
        })
    
    return render_template('ver_cliente.html', cliente=cliente, fichas=fichas_com_medicamentos)

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        telefone = request.form['telefone']
        
        if not validar_email(email):
            flash('Email inválido!', 'error')
            return redirect(url_for('editar', id=id))
        
        try:
            cursor.execute('BEGIN IMMEDIATE')
            cursor.execute('''
                UPDATE clientes 
                SET nome=?, email=?, telefone=?
                WHERE id=?
            ''', (nome, email, telefone, id))
            conn.commit()
            flash('Cliente atualizado com sucesso!', 'success')
            return redirect(url_for('ver_cliente', cliente_id=id))
        except Exception as e:
            conn.rollback()
            flash(f'Erro ao atualizar: {str(e)}', 'error')
            return redirect(url_for('editar', id=id))
    
    cursor.execute('SELECT * FROM clientes WHERE id=?', (id,))
    cliente = cursor.fetchone()
    return render_template('editar.html', cliente=cliente)

@app.route('/editar-ficha/<int:ficha_id>', methods=['GET', 'POST'])
def editar_ficha(ficha_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT f.*, c.nome, c.cpf
        FROM fichas f
        JOIN clientes c ON f.cliente_id = c.id
        WHERE f.id = ?
    ''', (ficha_id,))
    ficha = cursor.fetchone()
    
    if not ficha:
        flash('Ficha não encontrada!', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        data_entrada = request.form['data_entrada']
        data_saida = request.form['data_saida'] if request.form['data_saida'] else None
        observacoes = request.form.get('observacoes', '')
        
        medicamentos_json = request.form.get('medicamentos_data', '[]')
        try:
            medicamentos = json.loads(medicamentos_json)
        except:
            medicamentos = []
        
        try:
            cursor.execute('BEGIN IMMEDIATE')
            
            cursor.execute('''
                UPDATE fichas
                SET data_entrada=?, data_saida=?, observacoes=?
                WHERE id=?
            ''', (data_entrada, data_saida, observacoes, ficha_id))
            
            
            cursor.execute('DELETE FROM medicamentos WHERE ficha_id=?', (ficha_id,))
            
            for med in medicamentos:
                if med.get('nome') and med.get('dosagem'):
                    cursor.execute('''
                        INSERT INTO medicamentos (ficha_id, nome, dosagem, frequencia, observacoes)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (ficha_id, med['nome'], med['dosagem'], med.get('frequencia', ''), med.get('observacoes', '')))
            
            conn.commit()
            flash('Ficha atualizada com sucesso!', 'success')
            return redirect(url_for('ver_cliente', cliente_id=ficha[1]))
        except Exception as e:
            conn.rollback()
            flash(f'Erro ao atualizar ficha: {str(e)}', 'error')
            return redirect(url_for('editar_ficha', ficha_id=ficha_id))
    
   
    cursor.execute('SELECT * FROM medicamentos WHERE ficha_id=?', (ficha_id,))
    medicamentos = cursor.fetchall()
    
    return render_template('editar_ficha.html', ficha=ficha, medicamentos=medicamentos)

@app.route('/deletar/<int:id>')
def deletar(id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('BEGIN IMMEDIATE')
        cursor.execute('DELETE FROM clientes WHERE id=?', (id,))
        conn.commit()
        flash('Cliente removido com sucesso!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Erro ao deletar: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/deletar-ficha/<int:ficha_id>')
def deletar_ficha(ficha_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT cliente_id FROM fichas WHERE id=?', (ficha_id,))
        result = cursor.fetchone()
        
        if result:
            cliente_id = result[0]
            cursor.execute('BEGIN IMMEDIATE')
            cursor.execute('DELETE FROM fichas WHERE id=?', (ficha_id,))
            conn.commit()
            flash('Ficha removida com sucesso!', 'success')
            return redirect(url_for('ver_cliente', cliente_id=cliente_id))
    except Exception as e:
        conn.rollback()
        flash(f'Erro ao deletar ficha: {str(e)}', 'error')
    
    flash('Ficha não encontrada!', 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
