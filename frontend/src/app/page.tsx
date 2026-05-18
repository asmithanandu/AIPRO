"use client";

import { useState, useEffect, useRef } from "react";
import { socket } from "@/lib/socket";
import { Send, Bot, User, Menu, Plus, Settings, Paperclip, Loader2 } from "lucide-react";

interface Message {
  id: string;
  role: "user" | "ai";
  content: string;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    socket.connect();

    socket.on("chat:metadata", ({ conversation_id }) => {
      if (!conversationId) setConversationId(conversation_id);
    });

    socket.on("chat:queued", ({ jobId }) => {
      setIsTyping(true);
      setMessages((prev) => [
        ...prev,
        { id: jobId, role: "ai", content: "" },
      ]);
    });

    socket.on("chat:token", (token) => {
      setMessages((prev) => {
        const last = prev[prev.length - 1];
        if (last && last.role === "ai") {
          return [
            ...prev.slice(0, -1),
            { ...last, content: last.content + token },
          ];
        }
        return prev;
      });
    });

    socket.on("chat:complete", () => {
      setIsTyping(false);
    });

    socket.on("chat:error", ({ message }) => {
      setIsTyping(false);
      setMessages((prev) => [
        ...prev,
        { id: Date.now().toString(), role: "ai", content: `Error: ${message}` },
      ]);
    });

    return () => {
      socket.disconnect();
      socket.off("chat:metadata");
      socket.off("chat:queued");
      socket.off("chat:token");
      socket.off("chat:complete");
      socket.off("chat:error");
    };
  }, [conversationId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isTyping) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
    };

    setMessages((prev) => [...prev, userMessage]);
    socket.emit("chat:message", { prompt: input, conversation_id: conversationId });
    setInput("");
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      // Use relative path so Vercel's proxy catches it
      const res = await fetch("/api/documents/upload", {
        method: "POST",
        body: formData,
      });
      if (res.ok) {
        setMessages((prev) => [
          ...prev,
          { id: Date.now().toString(), role: "ai", content: `System: Successfully uploaded and processed ${file.name} for Retrieval-Augmented Generation.` }
        ]);
      }
    } catch (error) {
      console.error("Upload failed", error);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="flex h-screen bg-[#0E1117] text-white font-sans overflow-hidden">
      {/* Sidebar */}
      <div className="w-64 bg-[#161B22] border-r border-[#30363D] flex flex-col hidden md:flex">
        <div className="p-4 flex items-center gap-2 font-bold text-xl tracking-tight border-b border-[#30363D]">
          <Bot className="text-blue-500" />
          NexusAI
        </div>
        
        <div className="p-3">
          <button 
            onClick={() => { setMessages([]); setConversationId(null); }}
            className="flex items-center justify-center gap-2 w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors font-medium text-sm"
          >
            <Plus size={16} /> New Chat
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-3">
          <div className="text-xs text-gray-400 font-semibold mb-2 px-2 uppercase tracking-wider">Recent</div>
          <div className="px-2 py-2 text-sm text-gray-300 hover:bg-[#21262D] rounded cursor-pointer truncate">
            Current Session
          </div>
        </div>

        <div className="p-4 border-t border-[#30363D] flex items-center gap-3 text-sm cursor-pointer hover:bg-[#21262D] transition-colors">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-purple-500 to-blue-500 flex items-center justify-center text-white font-bold">
            U
          </div>
          <span className="font-medium">User Account</span>
          <Settings size={16} className="ml-auto text-gray-400" />
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col h-full bg-[#0D1117]">
        {/* Mobile Header */}
        <div className="md:hidden flex items-center justify-between p-4 border-b border-[#30363D] bg-[#161B22]">
          <div className="flex items-center gap-2 font-bold text-lg">
            <Bot className="text-blue-500" /> NexusAI
          </div>
          <button><Menu /></button>
        </div>

        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center opacity-70">
              <Bot size={48} className="text-blue-500 mb-4" />
              <h1 className="text-3xl font-bold mb-2">How can I help you today?</h1>
              <p className="max-w-md text-gray-400">NexusAI is an advanced cognitive orchestrator powered by Gemini. You can attach documents to chat with them.</p>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto w-full space-y-6">
              {messages.map((msg, idx) => (
                <div key={idx} className={`flex gap-4 ${msg.role === "user" ? "justify-end" : ""}`}>
                  {msg.role === "ai" && (
                    <div className="w-8 h-8 rounded bg-blue-600 flex items-center justify-center shrink-0 mt-1">
                      <Bot size={18} />
                    </div>
                  )}
                  <div className={`max-w-[85%] rounded-2xl px-5 py-3 ${
                    msg.role === "user" 
                      ? "bg-[#238636] text-white" 
                      : "bg-[#161B22] text-gray-200 border border-[#30363D]"
                  }`}>
                    {msg.content || <span className="animate-pulse">...</span>}
                  </div>
                  {msg.role === "user" && (
                    <div className="w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center shrink-0 mt-1">
                      <User size={18} />
                    </div>
                  )}
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="p-4 md:p-6 bg-gradient-to-t from-[#0D1117] to-transparent">
          <div className="max-w-3xl mx-auto relative">
            <form onSubmit={handleSend} className="relative flex items-center">
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileUpload}
                className="hidden"
                accept=".txt,.pdf,.md"
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading}
                className="absolute left-3 p-2 rounded-lg hover:bg-[#30363D] text-gray-400 transition-colors z-10"
                title="Upload Document for RAG"
              >
                {isUploading ? <Loader2 size={18} className="animate-spin" /> : <Paperclip size={18} />}
              </button>
              
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Message NexusAI... (or attach a document)"
                className="w-full bg-[#161B22] border border-[#30363D] text-white rounded-xl py-4 pl-12 pr-12 focus:outline-none focus:ring-2 focus:ring-blue-500 shadow-lg"
                disabled={isTyping}
              />
              <button
                type="submit"
                disabled={!input.trim() || isTyping}
                className="absolute right-3 p-2 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:hover:bg-blue-600 transition-colors"
              >
                <Send size={18} />
              </button>
            </form>
            <div className="text-center text-xs text-gray-500 mt-2">
              NexusAI can make mistakes. Context and Memory systems are actively engaged.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
