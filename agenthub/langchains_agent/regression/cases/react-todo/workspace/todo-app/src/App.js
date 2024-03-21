import React, { useState } from 'react';
function App() {
  const [todos, setTodos] = useState([]);
  const addTodo = task => {
    if (task) {
      const newItem = {
        id: todos.length + 1,
        task: task,
        completed: false
      };
      setTodos([...todos, newItem]);
    }
  };
  const toggleTodo = id => {
    setTodos(
      todos.map(todo =>
        todo.id === id ? { ...todo, completed: !todo.completed } : todo
      )
    );
  };
  return (
    <div className='App'>
      <h1>TODO List</h1>
      <AddTodo addTodo={addTodo} />
      <TodoList todos={todos} toggleTodo={toggleTodo} />
    </div>
  );
}

function AddTodo({ addTodo }) {
  const [task, setTask] = useState('');
  const handleSubmit = e => {
    e.preventDefault();
    addTodo(task);
    setTask('');
  };
  return (
    <form onSubmit={handleSubmit}>
      <input
        type='text'
        placeholder='Add new todo'
        value={task}
        onChange={e => setTask(e.target.value)}
      />
      <button type='submit'>Add</button>
    </form>
  );
}

function TodoList({ todos, toggleTodo }) {
  return (
    <ul>
      {todos.map(todo => (
        <TodoItem key={todo.id} todo={todo} toggleTodo={toggleTodo} />
      ))}
    </ul>
  );
}

function TodoItem({ todo, toggleTodo }) {
  return (
    <li
      style={{ textDecoration: todo.completed ? 'line-through' : 'none' }}
      onClick={() => toggleTodo(todo.id)}
    >
      {todo.task}
    </li>
  );
}

export default App;
