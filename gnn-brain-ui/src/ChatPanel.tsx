import React, { useState, useEffect, useRef } from "react";
import "./ChatPanel.css";

interface ChatPanelProps {
    nodeId: string | null;
    nodeLabel: string | null;
    backendUrl: string;
    onSourcesReturned?: (sources: string[]) => void;
}

interface Message {
    text: string;
    sender: "user" | "bot";
}

const ChatPanel: React.FC<ChatPanelProps> = ({ nodeId, nodeLabel, backendUrl, onSourcesReturned }) => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputText, setInputText] = useState("");
    const [loading, setLoading] = useState(false);
    const chatEndRef = useRef<HTMLDivElement>(null);

    // Load messages when node changes
    useEffect(() => {
        if (!nodeId) return;
        setMessages([]);
        setLoading(true);

        fetch(`${backendUrl}/messages?nodeId=${encodeURIComponent(nodeId)}`)
            .then((res) => res.json())
            .then((data) => {
                const history = (data.messages || []).map((m: any) => ({
                    text: m.text,
                    sender: m.sender || "user", // default to user if missing
                }));
                setMessages(history);
            })
            .catch((err) => console.error(err))
            .finally(() => setLoading(false));
    }, [nodeId, backendUrl]);

    // Auto-scroll
    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const handleSend = async () => {
        if (!inputText.trim() || !nodeId) return;

        const text = inputText.trim();
        setInputText("");

        // Optimistic update for user message
        const userMsg: Message = { text, sender: "user" };
        setMessages((prev) => [...prev, userMsg]);
        setLoading(true);

        try {
            const res = await fetch(`${backendUrl}/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ node: nodeLabel, query: text }),
            });

            if (res.ok) {
                const data = await res.json();
                // Add bot response
                if (data.answer) {
                    const botMsg: Message = {
                        text: data.answer,
                        sender: "bot"
                    };
                    setMessages((prev) => [...prev, botMsg]);
                    
                    if (onSourcesReturned && data.sources) {
                        onSourcesReturned(data.sources);
                    }
                }
            }
        } catch (err) {
            console.error("Failed to send message", err);
        } finally {
            setLoading(false);
        }
    };

    if (!nodeId) {
        return (
            <div className="chat-panel empty">
                <div className="empty-state">
                    <h3>No Node Selected</h3>
                    <p>Click on a node in the 3D graph to start a conversation with it.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="chat-panel">
            <div className="chat-header">
                <h3>Chat with {nodeLabel}</h3>
                <span className="node-badge">{nodeId}</span>
            </div>

            <div className="chat-messages">
                {loading && <div className="loading-spinner">Loading history...</div>}
                {messages.length === 0 && !loading && (
                    <div className="empty-history">No messages yet. Say hello!</div>
                )}
                {messages.map((msg, idx) => (
                    <div key={idx} className={`message ${msg.sender}`}>
                        <div className="bubble">{msg.text}</div>
                    </div>
                ))}
                <div ref={chatEndRef} />
            </div>

            <div className="chat-input-area">
                <input
                    type="text"
                    placeholder="Type your message..."
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSend()}
                />
                <button onClick={handleSend} disabled={!inputText.trim()}>
                    ➤
                </button>
            </div>
        </div>
    );
};

export default ChatPanel;
