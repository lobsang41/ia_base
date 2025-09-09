document.addEventListener("DOMContentLoaded", () => {
  // Formulario para crear agente
  document
    .getElementById("create-agent-form")
    .addEventListener("submit", (e) => {
      e.preventDefault();
      const data = {
        name: document.getElementById("agent-name").value,
        backend: document.getElementById("agent-backend").value,
        model: document.getElementById("agent-model").value,
        system_prompt: document.getElementById("agent-prompt").value,
        forbidden_topics: document.getElementById("agent-forbidden").value,
        must_say_no: document.getElementById("agent-must-say-no").value,
        verbosity_level: parseInt(
          document.getElementById("agent-verbosity").value
        ),
        require_citation: document.getElementById("agent-citation").checked,
        max_words_response: parseInt(
          document.getElementById("agent-max-words").value
        ),
        language: document.getElementById("agent-language").value,
        extra_data: document.getElementById("agent-extra-data").value,
        allowed_topics: document.getElementById("agent-allowed-topics").value,
      };
      fetch("/create_agent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      })
        .then((response) => response.json())
        .then((data) => {
          alert(data.status || data.error);
          // Recargar la lista de agentes
          if (data.status) {
            // Limpiar formulario
            document.getElementById("create-agent-form").reset();
            // Recargar agentes
            loadAgents();
          }
        })
        .catch((error) => console.error("Error creando agente:", error));
    });

  // Formulario para agregar conocimiento
  document
    .getElementById("add-knowledge-form")
    .addEventListener("submit", (e) => {
      e.preventDefault();
      const data = {
        agent_name: document.getElementById("knowledge-agent").value,
        fact: document.getElementById("knowledge-fact").value,
        source: document.getElementById("knowledge-source").value,
      };
      fetch("/add_knowledge", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      })
        .then((response) => response.json())
        .then((data) => {
          alert(data.status || data.error);
          // Limpiar el formulario después del éxito
          if (data.status) {
            document.getElementById("knowledge-fact").value = "";
            document.getElementById("knowledge-source").value = "";
          }
        })
        .catch((error) =>
          console.error("Error agregando conocimiento:", error)
        );
    });

  // Función para actualizar el select de agentes en el formulario de conocimiento
  function updateKnowledgeAgentSelect(agents) {
    const select = document.getElementById("knowledge-agent");
    if (select) {
      select.innerHTML = "";
      agents.forEach((agent) => {
        const option = document.createElement("option");
        if (typeof agent === "object" && agent.name) {
          option.value = agent.name;
          option.textContent = agent.name;
        } else {
          option.value = agent;
          option.textContent = agent;
        }
        select.appendChild(option);
      });
    }
  }

  // Actualizar ambos selects cuando se cargan los agentes
  function updateAllAgentSelects(agents) {
    // Select principal del chat
    const chatSelect = document.getElementById("agent-select");
    if (chatSelect) {
      chatSelect.innerHTML = "";
      agents.forEach((agent) => {
        const option = document.createElement("option");
        if (typeof agent === "object" && agent.name) {
          option.value = agent.name;
          option.textContent = agent.name;
        } else {
          option.value = agent;
          option.textContent = agent;
        }
        chatSelect.appendChild(option);
      });
    }

    // Select del formulario de conocimiento
    updateKnowledgeAgentSelect(agents);
  }

  // Función para cargar agentes
  function loadAgents() {
    fetch("/list_agents")
      .then((response) => response.json())
      .then((data) => {
        if (data.error) {
          console.error("Error en /list_agents:", data.error);
          return;
        }
        console.debug("Agentes cargados:", data.agents);
        updateAllAgentSelects(data.agents);
      })
      .catch((error) => {
        console.error("Error cargando agentes:", error);
      });
  }

  // Cargar agentes al inicio y actualizar todos los selects
  loadAgents();
});

let abortController = null;
let currentBotMsg = null;

// Audio queue management
let audioQueue = [];
let isPlaying = false;

function playNextAudio() {
  if (audioQueue.length === 0 || isPlaying) return;

  isPlaying = true;
  const audioData = audioQueue.shift(); // Get the next audio from the queue

  if (audioData.backend === "web_speech") {
    const utterance = new SpeechSynthesisUtterance(audioData.text);
    utterance.lang = audioData.language;
    const voices = window.speechSynthesis.getVoices();
    const selectedVoice = voices.find(
      (v) =>
        v.lang.includes(audioData.language) &&
        v.name.toLowerCase().includes(audioData.voice.toLowerCase())
    );
    if (selectedVoice) {
      utterance.voice = selectedVoice;
      console.debug(`Voz seleccionada para Web Speech: ${selectedVoice.name}`);
    } else {
      console.warn(
        `No se encontró voz para idioma ${audioData.language} y voz ${audioData.voice}`
      );
    }
    utterance.onend = () => {
      isPlaying = false;
      playNextAudio(); // Play the next audio when this one finishes
    };
    window.speechSynthesis.speak(utterance);
  } else if (audioData.backend === "elevenlabs") {
    const audio = new Audio(
      `data:${audioData.mime_type};base64,${audioData.audio}`
    );
    audio.onended = () => {
      isPlaying = false;
      playNextAudio(); // Play the next audio when this one finishes
    };
    audio.play().catch((e) => {
      console.error("Error al reproducir audio ElevenLabs:", e);
      isPlaying = false;
      playNextAudio(); // Proceed to next audio on error
    });
  }
}

function queueAudio(audioData) {
  audioQueue.push(audioData);
  playNextAudio(); // Start playing if nothing is currently playing
}

function speakText(text, language = "es-MX", voice = "male") {
  if (!text) return;
  console.debug(
    `Encolando Web Speech con texto: ${text}, idioma: ${language}, voz: ${voice}`
  );
  queueAudio({ backend: "web_speech", text, language, voice });
}

function sendMessage() {
  const msgInput = document.getElementById("message");
  const agentSelect = document.getElementById("agent-select");
  const msg = msgInput.value.trim();
  const agent_name = agentSelect ? agentSelect.value : "DefaultAgent";
  if (!msg) return;

  const chatWindow = document.getElementById("chat-window");
  const userMsg = document.createElement("div");
  userMsg.classList.add("chat-bubble", "user-bubble");
  userMsg.textContent = `Tú: ${msg}`;
  chatWindow.appendChild(userMsg);
  chatWindow.scrollTop = chatWindow.scrollHeight;

  // Mostrar botón de detener
  document.getElementById("stop-btn").classList.remove("hidden");

  // Inicializa burbuja de IA
  currentBotMsg = document.createElement("div");
  currentBotMsg.classList.add("chat-bubble", "ai-bubble");
  currentBotMsg.textContent = `IA (${agent_name}): `;
  chatWindow.appendChild(currentBotMsg);
  chatWindow.scrollTop = chatWindow.scrollHeight;

  // Cancelar si ya hay una solicitud
  if (abortController) {
    abortController.abort();
  }
  abortController = new AbortController();

  fetch("/ai_response", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query: msg, agent_name: agent_name }),
    signal: abortController.signal,
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let responseText = "";
      function readStream() {
        reader
          .read()
          .then(({ done, value }) => {
            if (done) {
              if (!responseText) {
                currentBotMsg.textContent = `IA (${agent_name}): No tengo información sobre eso.`;
              }
              document.getElementById("stop-btn").classList.add("hidden");
              abortController = null;
              return;
            }
            const chunk = decoder.decode(value);
            const lines = chunk.split("\n").filter((line) => line.trim());
            lines.forEach((line) => {
              try {
                const data = JSON.parse(line);
                console.debug("Respuesta recibida:", data);
                if (data.response) {
                  responseText += data.response;
                  currentBotMsg.textContent = `IA (${data.agent}): ${responseText}`;
                  if (data.audio && data.audio.backend === "elevenlabs") {
                    console.debug("Encolando audio ElevenLabs:", data.audio);
                    queueAudio(data.audio); // Queue ElevenLabs audio
                  } else if (
                    data.audio &&
                    data.audio.backend === "web_speech"
                  ) {
                    console.debug("Encolando audio Web Speech:", data.audio);
                    queueAudio(data.audio); // Queue Web Speech audio
                  }
                } else if (data.chunk) {
                  responseText += data.chunk;
                  currentBotMsg.textContent = `IA (${data.agent}): ${responseText}`;
                  if (data.audio && data.audio.backend === "elevenlabs") {
                    console.debug(
                      "Encolando audio ElevenLabs (chunk):",
                      data.audio
                    );
                    queueAudio(data.audio); // Queue ElevenLabs audio
                  } else if (
                    data.audio &&
                    data.audio.backend === "web_speech"
                  ) {
                    console.debug(
                      "Encolando audio Web Speech (chunk):",
                      data.audio
                    );
                    queueAudio(data.audio); // Queue Web Speech audio
                  }
                }
              } catch (e) {
                console.error("Error parseando chunk:", e, "Chunk:", line);
              }
            });
            chatWindow.scrollTop = chatWindow.scrollHeight;
            readStream();
          })
          .catch((error) => {
            if (error.name === "AbortError") {
              currentBotMsg.textContent = `IA (${agent_name}): Consulta detenida.`;
            } else {
              console.error("Error:", error);
              currentBotMsg.textContent = `IA (${agent_name}): Error en la respuesta: ${error.message}`;
            }
            chatWindow.scrollTop = chatWindow.scrollHeight;
            document.getElementById("stop-btn").classList.add("hidden");
            abortController = null;
          });
      }
      readStream();
    })
    .catch((error) => {
      if (error.name === "AbortError") {
        currentBotMsg.textContent = `IA (${agent_name}): Consulta detenida.`;
      } else {
        console.error("Error:", error);
        currentBotMsg.textContent = `IA (${agent_name}): Error en la respuesta: ${error.message}`;
      }
      chatWindow.scrollTop = chatWindow.scrollHeight;
      document.getElementById("stop-btn").classList.add("hidden");
      abortController = null;
    });

  msgInput.value = "";
}

window.speechSynthesis.onvoiceschanged = () => {
  console.debug(
    "Voces de Web Speech cargadas:",
    window.speechSynthesis.getVoices().map((v) => v.name)
  );
};

function stopGeneration() {
  if (abortController) {
    abortController.abort();
    document.getElementById("stop-btn").classList.add("hidden");
    abortController = null;
  }
  // Stop any ongoing audio playback
  window.speechSynthesis.cancel(); // Stop Web Speech
  audioQueue = []; // Clear the audio queue
  isPlaying = false; // Reset playback state
}
