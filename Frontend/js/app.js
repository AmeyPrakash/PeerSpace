// PeerSpace Comprehensive Client: Student-to-Student Live WebRTC Voice Chat, CBT Coach & Counselor Portal

document.addEventListener("DOMContentLoaded", () => {
    // -------------------------------------------------------------
    // 1. Navigation & DOM Elements
    // -------------------------------------------------------------
    const tabStudent = document.getElementById("tab-student");
    const tabAdmin = document.getElementById("tab-admin");
    const studentView = document.getElementById("student-view");
    const adminView = document.getElementById("admin-view");
    const applyCounselorView = document.getElementById("apply-counselor-view");
    const adminAlertCountBadge = document.getElementById("admin-alert-count");

    // Theme Toggle
    const themeToggleBtn = document.getElementById("theme-toggle-btn");
    const themeIconMoon = document.querySelector(".theme-icon-moon");
    const themeIconSun = document.querySelector(".theme-icon-sun");

    const currentTheme = localStorage.getItem("peerspace_theme") || "light";
    if (currentTheme === "dark") {
        document.documentElement.setAttribute("data-theme", "dark");
        if (themeIconMoon) themeIconMoon.style.display = "none";
        if (themeIconSun) themeIconSun.style.display = "block";
    }

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener("click", () => {
            let theme = document.documentElement.getAttribute("data-theme");
            if (theme === "dark") {
                document.documentElement.removeAttribute("data-theme");
                localStorage.setItem("peerspace_theme", "light");
                if (themeIconMoon) themeIconMoon.style.display = "block";
                if (themeIconSun) themeIconSun.style.display = "none";
            } else {
                document.documentElement.setAttribute("data-theme", "dark");
                localStorage.setItem("peerspace_theme", "dark");
                if (themeIconMoon) themeIconMoon.style.display = "none";
                if (themeIconSun) themeIconSun.style.display = "block";
            }
        });
    }

    // Student Identity
    const studentAliasBadge = document.getElementById("student-alias-badge");
    const currentAliasText = document.getElementById("current-alias-text");
    const heroAliasName = document.getElementById("hero-alias-name");

    // Chat Elements
    const chatMessages = document.getElementById("chat-messages");
    const chatForm = document.getElementById("chat-form");
    const messageInput = document.getElementById("message-input");
    const sendButton = document.getElementById("send-button");
    const typingRow = document.getElementById("typing-row");
    const heroIntro = document.getElementById("hero-intro");
    const newChatBtn = document.getElementById("new-chat-btn");

    // Student-to-Student Voice Call Elements
    const startCallBtn = document.getElementById("start-call-btn");
    const heroCallBtn = document.getElementById("hero-call-btn");
    const contactCounselorBtn = document.getElementById("contact-counselor-btn");
    const heroVoiceTrigger = document.getElementById("hero-voice-trigger");
    const inputCallBtn = document.getElementById("input-call-btn");

    const voiceCallOverlay = document.getElementById("voice-call-overlay");
    const callLivePill = document.getElementById("call-live-pill");
    const callConnectionBadge = document.getElementById("call-connection-badge");
    const callDurationTimer = document.getElementById("call-duration-timer");
    const callPeerLabel = document.getElementById("call-peer-label");

    const matchmakingStage = document.getElementById("matchmaking-stage");
    const matchmakingStatusHeading = document.getElementById("matchmaking-status-heading");
    const activePeerStage = document.getElementById("active-peer-stage");

    const localOrbWrapper = document.getElementById("local-orb-wrapper");
    const localPeerName = document.getElementById("local-peer-name");
    const localActivityLabel = document.getElementById("local-activity-label");

    const remoteOrbWrapper = document.getElementById("remote-orb-wrapper");
    const remotePeerName = document.getElementById("remote-peer-name");
    const remoteActivityLabel = document.getElementById("remote-activity-label");
    const remotePeerAudio = document.getElementById("remote-peer-audio");

    const callMuteBtn = document.getElementById("call-mute-btn");
    const muteBtnLabel = document.getElementById("mute-btn-label");
    const callNextPeerBtn = document.getElementById("call-next-peer-btn");
    const callCounselorAlertBtn = document.getElementById("call-counselor-alert-btn");
    const endVoiceCallBtn = document.getElementById("end-voice-call-btn");

    // Crisis Modal
    const crisisLink = document.getElementById("crisis-link");
    const crisisModal = document.getElementById("crisis-modal");
    const closeCrisis = document.getElementById("close-crisis");

    // Admin Dashboard Elements
    const adminAuthGate = document.getElementById("admin-auth-gate");
    const adminAuthForm = document.getElementById("admin-auth-form");
    const adminPasskeyInput = document.getElementById("admin-passkey-input");
    const adminMainContent = document.getElementById("admin-main-content");
    const adminLogoutBtn = document.getElementById("admin-logout-btn");
    const statActiveSessions = document.getElementById("stat-active-sessions");
    const statPendingAlerts = document.getElementById("stat-pending-alerts");
    const statTotalAlerts = document.getElementById("stat-total-alerts");
    const alertsFeed = document.getElementById("alerts-feed");
    const sessionsTableBody = document.getElementById("sessions-table-body");
    const refreshAlertsBtn = document.getElementById("refresh-alerts-btn");

    // -------------------------------------------------------------
    // 2. Global State & Identifiers
    // -------------------------------------------------------------
    const SESSION_PATTERN = /^[a-zA-Z0-9_-]{1,64}$/;
    let rawSessionId = localStorage.getItem("peerspace_session_id");
    let sessionId = (rawSessionId && SESSION_PATTERN.test(rawSessionId)) ? rawSessionId : generateUUID();
    let currentAlias = localStorage.getItem("peerspace_alias") || "";
    let adminToken = sessionStorage.getItem("peerspace_admin_token") || null;
    let alertsPollInterval = null;

    function generateUUID() {
        if (window.crypto && window.crypto.randomUUID) {
            return window.crypto.randomUUID();
        }
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    // -------------------------------------------------------------
    // 3. Anonymous Identity Setup
    // -------------------------------------------------------------
    async function initStudentSession(randomize = false) {
        try {
            const res = await fetch("/api/auth/student", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    session_id: sessionId,
                    alias: randomize ? null : (currentAlias || null),
                    randomize: randomize
                })
            });
            const data = await res.json();
            sessionId = data.session_id;
            currentAlias = data.alias;
            localStorage.setItem("peerspace_session_id", sessionId);
            localStorage.setItem("peerspace_alias", currentAlias);
            
            if (currentAliasText) currentAliasText.textContent = currentAlias;
            if (heroAliasName) heroAliasName.textContent = currentAlias;
            if (localPeerName) localPeerName.textContent = `${currentAlias} (You)`;
        } catch (e) {
            console.error("Auth error:", e);
        }
    }
    initStudentSession();

    if (studentAliasBadge) {
        studentAliasBadge.addEventListener("click", async () => {
            studentAliasBadge.classList.add("spinning");
            await initStudentSession(true);
            setTimeout(() => studentAliasBadge.classList.remove("spinning"), 350);
        });
    }

    // -------------------------------------------------------------
    // 4. Panel Navigation (Student Space vs Counselor Portal)
    // -------------------------------------------------------------
    function switchToStudentView() {
        tabStudent.classList.add("active");
        tabAdmin.classList.remove("active");
        studentView.style.display = "flex";
        adminView.style.display = "none";
        if (applyCounselorView) applyCounselorView.style.display = "none";
        if (alertsPollInterval) clearInterval(alertsPollInterval);
    }

    function switchToAdminView() {
        tabAdmin.classList.add("active");
        tabStudent.classList.remove("active");
        studentView.style.display = "none";
        if (applyCounselorView) applyCounselorView.style.display = "none";
        adminView.style.display = "flex";

        if (adminToken) {
            adminAuthGate.style.display = "none";
            adminMainContent.style.display = "block";
            loadAdminDashboard();
            alertsPollInterval = setInterval(loadAdminDashboard, 5000);
        } else {
            adminAuthGate.style.display = "flex";
            adminMainContent.style.display = "none";
        }
    }

    tabStudent.addEventListener("click", switchToStudentView);
    tabAdmin.addEventListener("click", switchToAdminView);

    const showApplyBtn = document.getElementById("show-apply-view-btn");
    if (showApplyBtn) {
        showApplyBtn.addEventListener("click", () => {
            adminView.style.display = "none";
            if (applyCounselorView) applyCounselorView.style.display = "flex";
        });
    }

    const backToLoginBtn = document.getElementById("back-to-login-btn");
    if (backToLoginBtn) {
        backToLoginBtn.addEventListener("click", () => {
            if (applyCounselorView) applyCounselorView.style.display = "none";
            switchToAdminView();
        });
    }

    // -------------------------------------------------------------
    // 5. STUDENT-TO-STUDENT WEBRTC LIVE VOICE CHAT CONTROLLER
    // -------------------------------------------------------------
    class PeerVoiceChatManager {
        constructor(config = {}) {
            this.mode = config.mode || 'peer';
            this.customSignalSender = config.signalSender || null;
            this.ws = null;
            this.peerConnection = null;
            this.localStream = null;
            this.remoteStream = null;
            this.isMuted = false;
            this.currentPeerAlias = null;
            this.timerInterval = null;
            this.secondsElapsed = 0;
            this.audioContext = null;
            this.localAnalyser = null;
            this.remoteAnalyser = null;
            this.animationFrameId = null;

            this.rtcConfig = {
                iceServers: [
                    { urls: "stun:stun.l.google.com:19302" },
                    { urls: "stun:stun1.l.google.com:19302" }
                ]
            };
        }

        async startVoiceCall() {
            voiceCallOverlay.style.display = "flex";
            this.resetCallUI();
            matchmakingStage.style.display = "flex";
            activePeerStage.style.display = "none";
            matchmakingStatusHeading.textContent = "Connecting to voice network...";

            // 1. Get local microphone stream
            try {
                this.localStream = await navigator.mediaDevices.getUserMedia({
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true
                    },
                    video: false
                });
                this.setupLocalAudioVisualizer(this.localStream);
            } catch (err) {
                console.error("Microphone access denied:", err);
                alert("Microphone permission is required for peer voice chat. Please allow microphone access in your browser.");
                this.endVoiceCall();
                return;
            }

            if (this.mode === 'peer') {
                this.connectSignalingServer();
            } else {
                await this.initiatePeerConnection(arguments.length > 0 ? arguments[0] : true);
            }
        }

        sendSignal(data) {
            if (this.customSignalSender) {
                this.customSignalSender(data);
            } else if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify(data));
            }
        }

        connectSignalingServer() {
            const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
            const wsUrl = `${protocol}//${window.location.host}/ws/voice-room?session_id=${encodeURIComponent(sessionId)}&alias=${encodeURIComponent(currentAlias)}`;
            
            if (this.ws) {
                this.ws.close();
            }

            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                matchmakingStatusHeading.textContent = "Looking for an anonymous peer student...";
            };

            this.ws.onmessage = async (event) => {
                try {
                    const data = JSON.parse(event.data);
                    await this.handleSignalingMessage(data);
                } catch (e) {
                    console.error("Signal parsing error:", e);
                }
            };

            this.ws.onerror = (err) => {
                console.error("Voice signaling error:", err);
            };

            this.ws.onclose = () => {
                console.log("Voice signaling disconnected");
            };
        }

        async handleSignalingMessage(data) {
            const type = data.type;

            if (type === "waiting") {
                matchmakingStatusHeading.textContent = data.message || "Waiting for another campus peer...";
            } else if (type === "matched") {
                this.currentPeerAlias = data.peer_alias || "Anonymous Peer";
                await this.initiatePeerConnection(data.is_initiator);
            } else if (type === "offer") {
                await this.handleRemoteOffer(data.offer);
            } else if (type === "answer") {
                await this.handleRemoteAnswer(data.answer);
            } else if (type === "ice-candidate") {
                if (data.candidate && this.peerConnection) {
                    try {
                        await this.peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate));
                    } catch (e) {
                        console.warn("ICE candidate error:", e);
                    }
                }
            } else if (type === "peer_disconnected") {
                this.handlePeerLeft(data.message || "Peer student disconnected");
            }
        }

        async initiatePeerConnection(isInitiator) {
            matchmakingStage.style.display = "none";
            activePeerStage.style.display = "flex";

            callLivePill.classList.add("connected");
            callConnectionBadge.textContent = "Live 2-Way Voice";
            callPeerLabel.textContent = `Connected with ${this.currentPeerAlias}`;
            remotePeerName.textContent = this.currentPeerAlias;
            remoteActivityLabel.textContent = "Connected";

            this.startTimer();

            this.peerConnection = new RTCPeerConnection(this.rtcConfig);

            // Add local audio tracks
            if (this.localStream) {
                this.localStream.getTracks().forEach((track) => {
                    this.peerConnection.addTrack(track, this.localStream);
                });
            }

            // Handle incoming remote audio stream
            this.peerConnection.ontrack = (event) => {
                this.remoteStream = event.streams[0];
                if (remotePeerAudio) {
                    remotePeerAudio.srcObject = this.remoteStream;
                    remotePeerAudio.play().catch((e) => console.log("Auto-play prevented:", e));
                }
                this.setupRemoteAudioVisualizer(this.remoteStream);
            };

            // Handle ICE candidates
            this.peerConnection.onicecandidate = (event) => {
                if (event.candidate) {
                    this.sendSignal({
                        type: "ice-candidate",
                        candidate: event.candidate
                    });
                }
            };

            // If caller/initiator, create WebRTC SDP offer
            if (isInitiator) {
                try {
                    const offer = await this.peerConnection.createOffer({
                        offerToReceiveAudio: true
                    });
                    await this.peerConnection.setLocalDescription(offer);
                    this.sendSignal({
                        type: "offer",
                        offer: offer
                    });
                } catch (e) {
                    console.error("Create offer error:", e);
                }
            }
        }

        async handleRemoteOffer(offer) {
            if (!this.peerConnection) return;
            try {
                await this.peerConnection.setRemoteDescription(new RTCSessionDescription(offer));
                const answer = await this.peerConnection.createAnswer();
                await this.peerConnection.setLocalDescription(answer);
                this.sendSignal({
                    type: "answer",
                    answer: answer
                });
            } catch (e) {
                console.error("Handle offer error:", e);
            }
        }

        async handleRemoteAnswer(answer) {
            if (!this.peerConnection) return;
            try {
                await this.peerConnection.setRemoteDescription(new RTCSessionDescription(answer));
            } catch (e) {
                console.error("Handle answer error:", e);
            }
        }

        handlePeerLeft(message) {
            if (this.peerConnection) {
                this.peerConnection.close();
                this.peerConnection = null;
            }
            if (this.timerInterval) clearInterval(this.timerInterval);
            
            callLivePill.classList.remove("connected");
            callConnectionBadge.textContent = "Disconnected";
            callPeerLabel.textContent = message;
            remoteActivityLabel.textContent = "Left Call";
            remoteOrbWrapper.classList.remove("speaking");
        }

        setupLocalAudioVisualizer(stream) {
            try {
                if (!this.audioContext) {
                    this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
                }
                const source = this.audioContext.createMediaStreamSource(stream);
                this.localAnalyser = this.audioContext.createAnalyser();
                this.localAnalyser.fftSize = 64;
                source.connect(this.localAnalyser);
                this.startVolumeMonitoring();
            } catch (e) {
                console.warn("Audio visualizer setup error:", e);
            }
        }

        setupRemoteAudioVisualizer(stream) {
            try {
                if (!this.audioContext) {
                    this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
                }
                const source = this.audioContext.createMediaStreamSource(stream);
                this.remoteAnalyser = this.audioContext.createAnalyser();
                this.remoteAnalyser.fftSize = 64;
                source.connect(this.remoteAnalyser);
            } catch (e) {
                console.warn("Remote visualizer setup error:", e);
            }
        }

        startVolumeMonitoring() {
            const checkVolume = () => {
                if (this.localAnalyser && !this.isMuted) {
                    const data = new Uint8Array(this.localAnalyser.frequencyBinCount);
                    this.localAnalyser.getByteFrequencyData(data);
                    let sum = 0;
                    for (let i = 0; i < data.length; i++) sum += data[i];
                    const avg = sum / data.length;
                    if (avg > 15) {
                        localOrbWrapper.classList.add("speaking");
                        localActivityLabel.textContent = "Speaking...";
                    } else {
                        localOrbWrapper.classList.remove("speaking");
                        localActivityLabel.textContent = "Listening";
                    }
                }

                if (this.remoteAnalyser) {
                    const data = new Uint8Array(this.remoteAnalyser.frequencyBinCount);
                    this.remoteAnalyser.getByteFrequencyData(data);
                    let sum = 0;
                    for (let i = 0; i < data.length; i++) sum += data[i];
                    const avg = sum / data.length;
                    if (avg > 15) {
                        remoteOrbWrapper.classList.add("speaking");
                        remoteActivityLabel.textContent = "Speaking...";
                    } else {
                        remoteOrbWrapper.classList.remove("speaking");
                        remoteActivityLabel.textContent = "Listening";
                    }
                }

                this.animationFrameId = requestAnimationFrame(checkVolume);
            };
            checkVolume();
        }

        toggleMute() {
            this.isMuted = !this.isMuted;
            if (this.localStream) {
                this.localStream.getAudioTracks().forEach((t) => (t.enabled = !this.isMuted));
            }
            if (this.isMuted) {
                callMuteBtn.classList.add("active-muted");
                muteBtnLabel.textContent = "Unmute";
                localOrbWrapper.classList.add("muted");
                localActivityLabel.textContent = "Muted";
            } else {
                callMuteBtn.classList.remove("active-muted");
                muteBtnLabel.textContent = "Mute";
                localOrbWrapper.classList.remove("muted");
                localActivityLabel.textContent = "Ready";
            }
        }

        nextPeer() {
            if (this.peerConnection) {
                this.peerConnection.close();
                this.peerConnection = null;
            }
            if (this.timerInterval) clearInterval(this.timerInterval);

            this.resetCallUI();
            matchmakingStage.style.display = "flex";
            activePeerStage.style.display = "none";
            matchmakingStatusHeading.textContent = "Finding another campus peer...";

            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({ type: "next-peer" }));
            } else {
                this.connectSignalingServer();
            }
        }

        async alertCounselor() {
            const confirmed = confirm("Request emergency counselor support for this peer voice session? An on-call counselor will be notified immediately.");
            if (!confirmed) return;

            try {
                const res = await fetch("/api/voice/escalate", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        session_id: sessionId,
                        alias: currentAlias,
                        peer_alias: this.currentPeerAlias || "Peer Student",
                        reason: "Student requested counselor intervention during peer voice chat."
                    })
                });
                if (res.ok) {
                    alert("Counselor alert dispatched. Campus staff has been notified of this voice session.");
                    checkAlertBadge();
                }
            } catch (e) {
                console.error("Escalation error:", e);
            }
        }

        startTimer() {
            this.secondsElapsed = 0;
            if (this.timerInterval) clearInterval(this.timerInterval);
            this.timerInterval = setInterval(() => {
                this.secondsElapsed++;
                const mins = String(Math.floor(this.secondsElapsed / 60)).padStart(2, '0');
                const secs = String(this.secondsElapsed % 60).padStart(2, '0');
                callDurationTimer.textContent = `${mins}:${secs}`;
            }, 1000);
        }

        resetCallUI() {
            this.secondsElapsed = 0;
            callDurationTimer.textContent = "00:00";
            callLivePill.classList.remove("connected");
            callConnectionBadge.textContent = "Matching...";
            callPeerLabel.textContent = "Searching for peer...";
            localOrbWrapper.className = "peer-orb-wrapper";
            remoteOrbWrapper.className = "peer-orb-wrapper";
            this.isMuted = false;
            callMuteBtn.classList.remove("active-muted");
            muteBtnLabel.textContent = "Mute";
        }

        endVoiceCall() {
            if (this.peerConnection) {
                this.peerConnection.close();
                this.peerConnection = null;
            }
            if (this.ws) {
                this.ws.close();
                this.ws = null;
            }
            if (this.localStream) {
                this.localStream.getTracks().forEach((track) => track.stop());
                this.localStream = null;
            }
            if (this.timerInterval) clearInterval(this.timerInterval);
            if (this.animationFrameId) cancelAnimationFrame(this.animationFrameId);

            voiceCallOverlay.style.display = "none";
            this.resetCallUI();
        }
    }

    const peerVoiceChatManager = new PeerVoiceChatManager();

    // -------------------------------------------------------------
    // Peer-to-Peer Text Chat Manager
    // -------------------------------------------------------------
    class PeerTextChatManager {
        constructor() {
            this.ws = null;
            this.active = false;
            this.peerAlias = null;
            this.peerTextConnectedBanner = document.getElementById("peer-text-connected-banner");
            this.peerTextStatus = document.getElementById("peer-text-status");
        }

        isActive() {
            return this.active;
        }

        startTextChat() {
            if (this.ws) this.ws.close();
            
            if (heroIntro) heroIntro.style.display = "none";
            if (this.peerTextConnectedBanner) this.peerTextConnectedBanner.style.display = "flex";
            if (this.peerTextStatus) this.peerTextStatus.textContent = "Finding an anonymous campus peer...";
            this.active = true;

            appendMessage("coach", "Looking for a peer to chat with...", "System");

            const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
            this.ws = new WebSocket(`${protocol}//${window.location.host}/api/ws/chat-room?session_id=${encodeURIComponent(sessionId)}&alias=${encodeURIComponent(currentAlias)}`);
            
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === "matched") {
                    this.peerAlias = data.peer_alias;
                    if (this.peerTextStatus) this.peerTextStatus.textContent = `Connected to Anonymous Peer.`;
                    appendMessage("coach", `You are now connected to an anonymous peer. Say hi!`, "System");
                } else if (data.type === "waiting") {
                    if (this.peerTextStatus) this.peerTextStatus.textContent = "Finding an anonymous campus peer...";
                } else if (data.type === "chat_message") {
                    appendMessage("coach", data.message, "Peer");
                } else if (data.type === "peer_disconnected") {
                    if (this.peerTextStatus) this.peerTextStatus.textContent = "Peer disconnected. Finding a new peer...";
                    appendMessage("coach", "Your peer left the chat.", "System");
                    this.startTextChat(); // re-queue
                }
            };
            
            this.ws.onclose = () => {
                if (this.active) {
                    if (this.peerTextStatus) this.peerTextStatus.textContent = "Disconnected from matchmaking.";
                }
            };
        }

        sendMessage(text) {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({
                    type: "chat_message",
                    message: text
                }));
            }
        }

        nextPeer() {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({ type: "next-peer" }));
                if (this.peerTextStatus) this.peerTextStatus.textContent = "Finding an anonymous campus peer...";
                appendMessage("coach", "Looking for a new peer...", "System");
            } else {
                this.startTextChat();
            }
        }

        disconnect() {
            this.active = false;
            if (this.ws) {
                this.ws.close();
                this.ws = null;
            }
            if (this.peerTextConnectedBanner) this.peerTextConnectedBanner.style.display = "none";
            appendMessage("coach", "Disconnected from peer text chat. You are back with the CBT coach.", "System");
        }
    }

    const peerTextChatManager = new PeerTextChatManager();

    const startChatBtn = document.getElementById("start-chat-btn");
    const heroStartChatBtn = document.getElementById("hero-start-chat-btn");
    const disconnectPeerTextBtn = document.getElementById("disconnect-peer-text-btn");
    const nextPeerTextBtn = document.getElementById("next-peer-text-btn");

    if (startChatBtn) startChatBtn.addEventListener("click", () => { switchToStudentView(); peerTextChatManager.startTextChat(); });
    if (heroStartChatBtn) heroStartChatBtn.addEventListener("click", () => { switchToStudentView(); peerTextChatManager.startTextChat(); });
    if (disconnectPeerTextBtn) disconnectPeerTextBtn.addEventListener("click", () => peerTextChatManager.disconnect());
    if (nextPeerTextBtn) nextPeerTextBtn.addEventListener("click", () => peerTextChatManager.nextPeer());

    // Voice Call Triggers
    if (startCallBtn) startCallBtn.addEventListener("click", () => peerVoiceChatManager.startVoiceCall());
    if (heroCallBtn) heroCallBtn.addEventListener("click", () => peerVoiceChatManager.startVoiceCall());
    if (inputCallBtn) inputCallBtn.addEventListener("click", () => peerVoiceChatManager.startVoiceCall());

    if (contactCounselorBtn) {
        const contactModal = document.getElementById("contact-modal");
        const closeContactModal = document.getElementById("close-contact-modal");
        const requestChatBtn = document.getElementById("request-chat-btn");
        const requestVoiceBtn = document.getElementById("request-voice-btn");
        const contactReasonInput = document.getElementById("contact-reason");

        if (contactModal) {
            contactCounselorBtn.addEventListener("click", () => {
                contactReasonInput.value = "";
                contactModal.style.display = "flex";
            });

            closeContactModal.addEventListener("click", () => {
                contactModal.style.display = "none";
            });

            const sendContactRequest = async (mode) => {
                const reason = contactReasonInput.value.trim() || "Student wants to talk.";
                contactModal.style.display = "none";
                contactCounselorBtn.textContent = "Requesting...";
                contactCounselorBtn.disabled = true;

                try {
                    const res = await fetch("/api/chat/escalate", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            session_id: sessionId,
                            alias: currentAlias,
                            reason: reason,
                            mode: mode
                        })
                    });
                    
                    if (res.ok) {
                        alert(`A counselor has been alerted for a ${mode} session. Please stay on this page, they will join shortly.`);
                        contactCounselorBtn.textContent = "Counselor Alerted";
                    } else {
                        contactCounselorBtn.textContent = "Contact Counselor Directly";
                        contactCounselorBtn.disabled = false;
                        alert("Failed to send request. Please try again.");
                    }
                } catch (err) {
                    console.error("Escalation error:", err);
                    contactCounselorBtn.textContent = "Contact Counselor Directly";
                    contactCounselorBtn.disabled = false;
                }
            };

            requestChatBtn.addEventListener("click", () => sendContactRequest("chat"));
            requestVoiceBtn.addEventListener("click", () => sendContactRequest("voice"));
        }
    }
    if (heroVoiceTrigger) heroVoiceTrigger.addEventListener("click", (e) => {
        if (e.target !== heroCallBtn) peerVoiceChatManager.startVoiceCall();
    });
    if (inputCallBtn) inputCallBtn.addEventListener("click", () => peerVoiceChatManager.startVoiceCall());

    // In-Call Controls
    callMuteBtn.addEventListener("click", () => peerVoiceChatManager.toggleMute());
    callNextPeerBtn.addEventListener("click", () => peerVoiceChatManager.nextPeer());
    callCounselorAlertBtn.addEventListener("click", () => peerVoiceChatManager.alertCounselor());
    endVoiceCallBtn.addEventListener("click", () => peerVoiceChatManager.endVoiceCall());

    // -------------------------------------------------------------
    // 6. Student Text Chat Interactions (with AI CBT Peer Coach)
    // -------------------------------------------------------------
    messageInput.addEventListener("input", () => {
        messageInput.style.height = "auto";
        messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + "px";
        sendButton.disabled = !messageInput.value.trim();
    });

    messageInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            const text = messageInput.value.trim();
            if (text && !sendButton.disabled) {
                sendChatMessage(text);
            }
        }
    });

    async function sendChatMessage(text) {
        if (!text) return;

        if (heroIntro) heroIntro.style.display = "none";

        appendMessage("user", text);
        messageInput.value = "";
        messageInput.style.height = "auto";
        sendButton.disabled = true;

        if (peerTextChatManager.isActive()) {
            peerTextChatManager.sendMessage(text);
            return;
        }

        setTyping(true);

        try {
            const res = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: text,
                    session_id: sessionId,
                    alias: currentAlias
                })
            });

            if (res.status === 429) {
                setTyping(false);
                appendMessage("coach", "You're typing super fast! Take a breath and wait a few seconds before sending another message.");
                return;
            }

            if (!res.ok) throw new Error("HTTP error " + res.status);

            const data = await res.json();
            setTyping(false);

            if (data.session_id && SESSION_PATTERN.test(data.session_id)) {
                sessionId = data.session_id;
                localStorage.setItem("peerspace_session_id", sessionId);
            }

            if (data.reply) {
                appendMessage("coach", data.reply);
            }

            checkAlertBadge();
        } catch (err) {
            console.error("Chat error:", err);
            setTyping(false);
            appendMessage("coach", "Hey, my connection dropped for a second. Could you repeat that?");
        }
    }

    // Attach click listeners to all starting prompt cards and chips
    document.querySelectorAll(".prompt-card, .chip").forEach((btn) => {
        btn.addEventListener("click", (e) => {
            e.preventDefault();
            const text = btn.getAttribute("data-text");
            if (text) {
                sendChatMessage(text);
            }
        });
    });

    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const text = messageInput.value.trim();
        if (text) {
            await sendChatMessage(text);
        }
    });

    function formatTime() {
        const d = new Date();
        return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    }

    function appendMessage(role, text, customName = null) {
        const unit = document.createElement("div");
        unit.className = `message-unit ${role}`;

        const bubble = document.createElement("div");
        bubble.className = "bubble";
        bubble.textContent = text;

        const time = document.createElement("div");
        time.className = "message-time";
        time.textContent = `${customName ? customName : (role === "user" ? (currentAlias || "You") : "Peer Coach")} - ${formatTime()}`;

        unit.appendChild(bubble);
        unit.appendChild(time);

        chatMessages.appendChild(unit);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function setTyping(visible) {
        if (visible) {
            typingRow.style.display = "flex";
            chatMessages.appendChild(typingRow);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        } else {
            typingRow.style.display = "none";
        }
    }

    newChatBtn.addEventListener("click", async () => {
        if (confirm("Start a new anonymous session and reset conversation?")) {
            try {
                await fetch("/api/reset", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ session_id: sessionId })
                });

                sessionId = generateUUID();
                localStorage.setItem("peerspace_session_id", sessionId);
                await initStudentSession();

                chatMessages.innerHTML = "";
                if (heroIntro) {
                    heroIntro.style.display = "block";
                    chatMessages.appendChild(heroIntro);
                }
            } catch (err) {
                console.error("Reset error:", err);
            }
        }
    });

    // -------------------------------------------------------------
    // 7. Counselor / Admin Portal Actions & LOGOUT
    // -------------------------------------------------------------
    adminAuthForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const passkey = adminPasskeyInput.value.trim();
        if (!passkey) return;

        try {
            const res = await fetch("/api/auth/admin", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ passkey: passkey })
            });

            if (!res.ok) {
                alert("Incorrect passkey. Please check authorized staff credentials.");
                return;
            }

            const data = await res.json();
            adminToken = data.token;
            sessionStorage.setItem("peerspace_admin_token", adminToken);

            adminAuthGate.style.display = "none";
            adminMainContent.style.display = "block";
            loadAdminDashboard();
            alertsPollInterval = setInterval(loadAdminDashboard, 5000);
        } catch (e) {
            alert("Authentication failed.");
        }
    });

    if (adminLogoutBtn) {
        adminLogoutBtn.addEventListener("click", () => {
            sessionStorage.removeItem("peerspace_admin_token");
            adminToken = null;
            if (alertsPollInterval) clearInterval(alertsPollInterval);
            
            adminPasskeyInput.value = "";
            adminAuthGate.style.display = "flex";
            adminMainContent.style.display = "none";
            switchToStudentView();
        });
    }

    refreshAlertsBtn.addEventListener("click", () => loadAdminDashboard());

    async function loadAdminDashboard() {
        try {
            const alertsRes = await fetch("/api/admin/alerts");
            const alertsData = await alertsRes.json();

            statPendingAlerts.textContent = alertsData.pending_count || 0;
            statTotalAlerts.textContent = alertsData.total_alerts || 0;

            if (alertsData.pending_count > 0) {
                adminAlertCountBadge.textContent = alertsData.pending_count;
                adminAlertCountBadge.style.display = "inline-block";
            } else {
                adminAlertCountBadge.style.display = "none";
            }

            renderAlerts(alertsData.alerts || []);

            const sessionsRes = await fetch("/api/admin/sessions");
            const sessionsData = await sessionsRes.json();
            statActiveSessions.textContent = sessionsData.total_active || 0;
            renderSessions(sessionsData.active_sessions || []);
        } catch (e) {
            console.error("Admin dashboard fetch error:", e);
        }
    }

    async function checkAlertBadge() {
        try {
            const alertsRes = await fetch("/api/admin/alerts");
            const data = await alertsRes.json();
            if (data.pending_count > 0) {
                adminAlertCountBadge.textContent = data.pending_count;
                adminAlertCountBadge.style.display = "inline-block";
            } else {
                adminAlertCountBadge.style.display = "none";
            }
        } catch (e) {}
    }

    function renderAlerts(alerts) {
        if (!alerts || alerts.length === 0) {
            alertsFeed.innerHTML = '<div class="empty-alerts">No active alerts. All sessions running normally.</div>';
            return;
        }

        alertsFeed.innerHTML = "";
        alerts.forEach((alert) => {
            const card = document.createElement("div");
            card.className = `alert-card ${alert.severity}`;

            card.innerHTML = `
                <div class="alert-head">
                    <div class="alert-title">
                        <span class="severity-tag ${alert.severity}">${alert.severity}</span>
                        <span>Student: ${alert.alias} (${alert.session_id.substring(0, 8)}...)</span>
                    </div>
                    <span class="alert-time">${alert.timestamp}</span>
                </div>
                <div class="alert-reason"><strong>Trigger Reason:</strong> ${alert.reason}</div>
                <div class="alert-recommendation"><strong>Action Protocol:</strong> ${alert.recommended_action}</div>
                <div class="alert-actions" id="actions-${alert.id}">
                    ${
                        alert.status === "PENDING"
                        ? `
                            <button class="dispatch-btn" data-id="${alert.id}" data-act="DISPATCHED">Dispatch On-Call Counselor</button>
                            <button class="resolve-btn" data-id="${alert.id}" data-act="RESOLVED">Mark Resolved</button>
                            <button class="btn-secondary join-counselor-alert-btn" data-session-id="${alert.session_id}" data-alert-id="${alert.id}" style="padding: 0.5rem 1rem; border-radius: 4px; border: 1px solid var(--border-color); background: var(--bg-card); cursor: pointer; color: var(--text-color);">Join Live Chat</button>
                          `
                        : `<span class="alert-status-badge ${alert.status}">Status: ${alert.status}</span>
                           <button class="btn-secondary join-counselor-alert-btn" data-session-id="${alert.session_id}" data-alert-id="${alert.id}" style="margin-left: 1rem; padding: 0.5rem 1rem; border-radius: 4px; border: 1px solid var(--border-color); background: var(--bg-card); cursor: pointer; color: var(--text-color);">Join Live Chat</button>`
                    }
                </div>
            `;

            card.querySelectorAll("button.dispatch-btn, button.resolve-btn").forEach((btn) => {
                btn.addEventListener("click", async () => {
                    const alertId = btn.getAttribute("data-id");
                    const act = btn.getAttribute("data-act");
                    await dispatchAlertAction(alertId, act);
                });
            });

            card.querySelectorAll(".join-counselor-alert-btn").forEach((btn) => {
                btn.addEventListener("click", async () => {
                    const sid = btn.getAttribute("data-session-id");
                    const alertId = btn.getAttribute("data-alert-id");
                    
                    // Automatically mark as DISPATCHED if a counselor joins
                    if (alert.status === "PENDING") {
                        await dispatchAlertAction(alertId, "DISPATCHED");
                    }
                    
                    openCounselorChat(sid);
                });
            });

            alertsFeed.appendChild(card);
        });
    }

    async function dispatchAlertAction(alertId, action) {
        try {
            const res = await fetch(`/api/admin/alerts/${alertId}/action`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ action: action })
            });
            if (res.ok) loadAdminDashboard();
        } catch (e) {
            console.error("Alert action error:", e);
        }
    }

    function renderSessions(sessions) {
        if (!sessions || sessions.length === 0) {
            sessionsTableBody.innerHTML = '<tr><td colspan="5" class="text-center">No active student sessions.</td></tr>';
            return;
        }

        sessionsTableBody.innerHTML = "";
        sessions.forEach((s) => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>${s.alias}</strong></td>
                <td><code>${s.session_id}</code></td>
                <td>${s.messages} msg(s)</td>
                <td>${s.last_active}</td>
                <td><button class="btn-secondary join-counselor-chat-btn" data-id="${s.full_id}" style="padding: 0.3rem 0.8rem; font-size: 0.8rem;">Join Chat</button></td>
            `;
            tr.querySelector('.join-counselor-chat-btn').addEventListener('click', () => {
                openCounselorChat(s.full_id);
            });
            sessionsTableBody.appendChild(tr);
        });
    }

    // -------------------------------------------------------------
    // 8. Crisis Modal Controls
    // -------------------------------------------------------------
    crisisLink.addEventListener("click", () => crisisModal.style.display = "flex");
    closeCrisis.addEventListener("click", () => crisisModal.style.display = "none");
    window.addEventListener("click", (e) => {
        if (e.target === crisisModal) crisisModal.style.display = "none";
    });

    checkAlertBadge();

    // -------------------------------------------------------------
    // 9. Counselor Live Chat Integration
    // -------------------------------------------------------------
    
    let studentWS = null;
    let counselorActive = false;
    const counselorConnectedBanner = document.getElementById("counselor-connected-banner");

    function initStudentPersistentWS() {
        if (studentWS) studentWS.close();
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        studentWS = new WebSocket(`${protocol}//${window.location.host}/ws/student?session_id=${encodeURIComponent(sessionId)}`);
        
        studentWS.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === "counselor_chat") {
                counselorActive = true;
                if (counselorConnectedBanner) counselorConnectedBanner.style.display = "flex";
                if (heroIntro) heroIntro.style.display = "none";
                
                const msgEl = document.createElement("div");
                msgEl.className = "message ai-message";
                msgEl.innerHTML = `
                    <div class="message-content" style="border: 1px solid #10b981;">
                        <span class="pastel-badge green" style="margin-bottom:0.5rem;display:inline-block">Human Counselor</span><br/>
                        ${data.message.replace(/\n/g, '<br/>')}
                    </div>
                `;
                chatMessages.appendChild(msgEl);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            } else if (data.type === "counselor_webrtc_signal") {
                if (!window.directVoiceChatManager) {
                    window.directVoiceChatManager = new PeerVoiceChatManager({
                        mode: 'student',
                        signalSender: (signalData) => {
                            if (studentWS && studentWS.readyState === WebSocket.OPEN) {
                                studentWS.send(JSON.stringify(signalData));
                            }
                        }
                    });
                    window.directVoiceChatManager.startVoiceCall(false, "Counselor");
                }
                window.directVoiceChatManager.handleSignalingMessage(data.signal);
            }
        };
    }
    
    initStudentPersistentWS();

    if (studentAliasBadge) {
        studentAliasBadge.addEventListener("click", () => {
            setTimeout(initStudentPersistentWS, 500); 
        });
    }
    
    chatForm.addEventListener("submit", (e) => {
        if (counselorActive && studentWS && studentWS.readyState === WebSocket.OPEN) {
            e.preventDefault(); 
            e.stopPropagation();
            
            const msg = messageInput.value.trim();
            if (!msg) return;
            
            const msgEl = document.createElement("div");
            msgEl.className = "message user-message";
            msgEl.innerHTML = `<div class="message-content">${msg}</div>`;
            chatMessages.appendChild(msgEl);
            messageInput.value = "";
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            studentWS.send(JSON.stringify({ type: "chat_reply", message: msg }));
        }
    }, true); 

    let counselorWS = null;
    let activeTargetSessionId = null;
    
    const counselorChatPanel = document.getElementById("counselor-chat-panel");
    const closeCounselorChatBtn = document.getElementById("close-counselor-chat-btn");
    const counselorChatMessages = document.getElementById("counselor-chat-messages");
    const counselorChatForm = document.getElementById("counselor-chat-form");
    const counselorMessageInput = document.getElementById("counselor-message-input");
    const counselorStartCallBtn = document.getElementById("counselor-start-call-btn");

    if (counselorStartCallBtn) {
        counselorStartCallBtn.addEventListener("click", () => {
            if (!activeTargetSessionId || !counselorWS) return;
            window.directVoiceChatManager = new PeerVoiceChatManager({
                mode: 'counselor',
                signalSender: (signalData) => {
                    signalData.session_id = activeTargetSessionId;
                    if (counselorWS && counselorWS.readyState === WebSocket.OPEN) {
                        counselorWS.send(JSON.stringify(signalData));
                    }
                }
            });
            window.directVoiceChatManager.startVoiceCall(true, "Student");
        });
    }

    function initCounselorWS() {
        if (counselorWS) counselorWS.close();
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        counselorWS = new WebSocket(`${protocol}//${window.location.host}/ws/counselor`);
        
        counselorWS.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === "student_chat_reply" && data.session_id === activeTargetSessionId) {
                const msgEl = document.createElement("div");
                msgEl.className = "message ai-message";
                msgEl.innerHTML = `
                    <div class="message-content">
                        <strong style="display:block; margin-bottom: 0.2rem; font-size: 0.8rem; color: var(--text-muted);">Student</strong>
                        ${data.message}
                    </div>
                `;
                counselorChatMessages.appendChild(msgEl);
                counselorChatMessages.scrollTop = counselorChatMessages.scrollHeight;
            } else if (data.type === "student_webrtc_signal" && data.session_id === activeTargetSessionId) {
                if (window.directVoiceChatManager) {
                    window.directVoiceChatManager.handleSignalingMessage(data.signal);
                }
            }
        };
    }

    function openCounselorChat(targetSessionId) {
        if (!counselorWS) initCounselorWS();
        activeTargetSessionId = targetSessionId;
        if (counselorChatPanel) counselorChatPanel.style.display = "block";
        if (counselorChatMessages) {
            counselorChatMessages.innerHTML = '<div class="empty-feed-text">Session connected. Send a message to start.</div>';
            counselorChatMessages.style.display = "flex";
            counselorChatMessages.style.flexDirection = "column";
        }
        if (counselorChatPanel) counselorChatPanel.scrollIntoView({ behavior: 'smooth' });
    }

    if (closeCounselorChatBtn) {
        closeCounselorChatBtn.addEventListener("click", () => {
            counselorChatPanel.style.display = "none";
            activeTargetSessionId = null;
        });
    }

    if (counselorChatForm) {
        counselorChatForm.addEventListener("submit", (e) => {
            e.preventDefault();
            const msg = counselorMessageInput.value.trim();
            if (!msg || !activeTargetSessionId || !counselorWS) return;
            
            const msgEl = document.createElement("div");
            msgEl.className = "message user-message";
            msgEl.innerHTML = `
                <div class="message-content">
                    <strong style="display:block; margin-bottom: 0.2rem; font-size: 0.8rem; opacity: 0.8;">You</strong>
                    ${msg}
                </div>
            `;
            counselorChatMessages.appendChild(msgEl);
            counselorMessageInput.value = "";
            counselorChatMessages.scrollTop = counselorChatMessages.scrollHeight;
            
            counselorWS.send(JSON.stringify({
                type: "counselor_chat",
                session_id: activeTargetSessionId,
                message: msg
            }));
        });
    }

    const counselorForm = document.getElementById("counselor-application-form");
    if (counselorForm) {
        counselorForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const submitBtn = counselorForm.querySelector("button[type='submit']");
            const originalText = submitBtn.textContent;
            submitBtn.textContent = "Submitting...";
            submitBtn.disabled = true;

            const formData = new FormData(counselorForm);
            const payload = {
                full_name: formData.get("full_name"),
                email: formData.get("email"),
                phone: formData.get("phone"),
                highest_degree: formData.get("highest_degree"),
                degree_field: formData.get("degree_field"),
                university: formData.get("university"),
                graduation_year: parseInt(formData.get("graduation_year")) || new Date().getFullYear(),
                certifications: formData.get("certifications") || "",
                years_of_experience: parseInt(formData.get("years_of_experience")) || 0,
                current_role: formData.get("current_role"),
                specializations: formData.getAll("specializations").join(", "),
                motivation: formData.get("motivation"),
                background_info: formData.get("background_info") || "",
                terms_accepted: formData.get("terms_accepted") === "on"
            };

            try {
                const response = await fetch("/api/counselor/apply", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(payload)
                });
                const result = await response.json();
                if (response.ok) {
                    counselorForm.style.display = "none";
                    const statusSection = document.querySelector("#counselor-application-status");
                    if (statusSection) statusSection.style.display = "none";
                    
                    const verificationSection = document.getElementById("post-submission-verification");
                    verificationSection.style.display = "block";
                    
                    document.getElementById("post-email-display").textContent = payload.email;
                    window.currentApplicationId = result.application_id;
                    window.currentEmail = payload.email;
                    
                    if (payload.phone && payload.phone.trim().length > 0) {
                        document.getElementById("post-phone-verification").style.display = "block";
                        document.getElementById("post-phone-display").textContent = payload.phone;
                        window.currentPhone = payload.phone;
                    }
                    
                    setupPostVerification();
                } else {
                    alert("Error: " + (result.detail || "Failed to submit application."));
                    submitBtn.textContent = originalText;
                    submitBtn.disabled = false;
                }
            } catch (err) {
                console.error(err);
                alert("Network error. Please try again later.");
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
            }
        });
    }

    function setupPostVerification() {
        const verifyEmailBtn = document.getElementById("post-verify-email-btn");
        const confirmEmailBtn = document.getElementById("post-confirm-email-otp-btn");
        const emailOtpContainer = document.getElementById("post-email-otp-container");
        const emailOtpInput = document.getElementById("post-email-otp-input");
        const emailHint = document.getElementById("post-email-hint");
        const emailVerified = document.getElementById("post-email-verified");

        const verifyPhoneBtn = document.getElementById("post-verify-phone-btn");
        const confirmPhoneBtn = document.getElementById("post-confirm-phone-otp-btn");
        const phoneOtpContainer = document.getElementById("post-phone-otp-container");
        const phoneOtpInput = document.getElementById("post-phone-otp-input");
        const phoneHint = document.getElementById("post-phone-hint");
        const phoneVerified = document.getElementById("post-phone-verified");

        const finalizeBtn = document.getElementById("finalize-application-btn");

        function checkCompletion() {
            const isEmailVerified = emailVerified.value === "true";
            const needsPhone = !!window.currentPhone;
            const isPhoneVerified = phoneVerified.value === "true";

            if (isEmailVerified && (!needsPhone || isPhoneVerified)) {
                finalizeBtn.style.display = "block";
            }
        }

        async function sendOtp(type, target, btn, container, hint) {
            btn.textContent = "Sending...";
            btn.disabled = true;
            try {
                const res = await fetch("/api/counselor/verify/send", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ type, target })
                });
                if (res.ok) {
                    container.style.display = "flex";
                    btn.textContent = "Sent";
                    hint.textContent = "Code sent! Check backend logs for the mock OTP.";
                } else {
                    const data = await res.json();
                    alert(data.detail || "Failed to send code");
                    btn.textContent = "Send Code";
                    btn.disabled = false;
                }
            } catch (e) {
                alert("Network error.");
                btn.textContent = "Send Code";
                btn.disabled = false;
            }
        }

        verifyEmailBtn.addEventListener("click", () => sendOtp("email", window.currentEmail, verifyEmailBtn, emailOtpContainer, emailHint));
        if (verifyPhoneBtn) verifyPhoneBtn.addEventListener("click", () => sendOtp("phone", window.currentPhone, verifyPhoneBtn, phoneOtpContainer, phoneHint));

        confirmEmailBtn.addEventListener("click", () => {
            if (emailOtpInput.value.trim().length === 6) {
                emailVerified.value = "true";
                emailOtpContainer.innerHTML = `<span style="color: var(--text-primary); font-family: var(--font-mono); font-size: 0.85rem; letter-spacing: 0.05em; text-transform: uppercase;">[Verified]</span>`;
                emailHint.style.display = "none";
                checkCompletion();
            } else {
                alert("Please enter a 6-digit code.");
            }
        });

        if (confirmPhoneBtn) {
            confirmPhoneBtn.addEventListener("click", () => {
                if (phoneOtpInput.value.trim().length === 6) {
                    phoneVerified.value = "true";
                    phoneOtpContainer.innerHTML = `<span style="color: var(--text-primary); font-family: var(--font-mono); font-size: 0.85rem; letter-spacing: 0.05em; text-transform: uppercase;">[Verified]</span>`;
                    phoneHint.style.display = "none";
                    checkCompletion();
                } else {
                    alert("Please enter a 6-digit code.");
                }
            });
        }

        finalizeBtn.addEventListener("click", async () => {
            finalizeBtn.textContent = "Verifying & Approving...";
            finalizeBtn.disabled = true;

            try {
                const payload = {
                    application_id: window.currentApplicationId,
                    email: window.currentEmail,
                    email_otp: emailOtpInput.value.trim(),
                };
                
                if (window.currentPhone) {
                    payload.phone = window.currentPhone;
                    payload.phone_otp = phoneOtpInput.value.trim();
                }

                const res = await fetch("/api/counselor/verify-application", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                
                const data = await res.json();
                if (res.ok) {
                    document.getElementById("post-email-verification").style.display = "none";
                    document.getElementById("post-phone-verification").style.display = "none";
                    finalizeBtn.style.display = "none";
                    
                    const revealContainer = document.getElementById("passkey-reveal-container");
                    const passkeyDisplay = document.getElementById("passkey-display");
                    
                    passkeyDisplay.textContent = data.passkey;
                    revealContainer.style.display = "block";
                } else {
                    alert("Error: " + (data.detail || "Verification failed."));
                    finalizeBtn.textContent = "Complete Application";
                    finalizeBtn.disabled = false;
                }
            } catch (err) {
                console.error(err);
                alert("Network error.");
                finalizeBtn.textContent = "Complete Application";
                finalizeBtn.disabled = false;
            }
        });
    }
});
