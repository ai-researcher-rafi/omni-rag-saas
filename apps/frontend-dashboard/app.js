document.getElementById('chatForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const inputEl = document.getElementById('userInput');
  const chatBox = document.getElementById('chatBox');
  const query = inputEl.value.trim();

  if (!query) return;

  // Append User Message
  const userMsg = document.createElement('div');
  userMsg.className = 'bg-blue-900/40 border border-blue-500/20 p-3 rounded-lg text-xs max-w-[80%] ml-auto text-right';
  userMsg.innerHTML = `<p class="text-teal-300 font-semibold mb-1">You</p>${query}`;
  chatBox.appendChild(userMsg);

  inputEl.value = '';
  chatBox.scrollTop = chatBox.scrollHeight;

  // Simulated RAG Engine Response
  setTimeout(() => {
    const aiMsg = document.createElement('div');
    aiMsg.className = 'bg-gray-800 p-3 rounded-lg text-xs max-w-[80%]';
    aiMsg.innerHTML = `<p class="text-blue-300 font-semibold mb-1">AI Assistant (Gemini 1.5 Flash)</p>Processing vector search for response...`;
    chatBox.appendChild(aiMsg);
    chatBox.scrollTop = chatBox.scrollHeight;
  }, 600);
});