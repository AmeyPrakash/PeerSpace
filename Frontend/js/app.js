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

    // Persistent WebSocket & Counselor Intervention State
    let studentWS = null;
    let counselorWS = null;
    let counselorActive = false;
    let activeTargetSessionId = null;
    let activeTargetAlias = null;
    let studentWSRetryTimer = null;
    let counselorWSRetryTimer = null;

    function escapeHtml(str) {
        if (!str) return "";
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

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
    async function initStudentSession(randomize = false, isPageLoad = false) {
        try {
            // On every page load (including Ctrl+R refresh), reset stale counselor state
            // so the student always starts fresh. The banner will only re-appear when
            // a counselor actively joins via the live WebSocket.
            if (isPageLoad && sessionId) {
                try {
                    await fetch("/api/reset", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ session_id: sessionId })
                    });
                } catch (e) { /* best-effort */ }
            }

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
            const prevSessionId = sessionId;
            sessionId = data.session_id;
            currentAlias = data.alias;
            localStorage.setItem("peerspace_session_id", sessionId);
            localStorage.setItem("peerspace_alias", currentAlias);

            if (currentAliasText) currentAliasText.textContent = currentAlias;
            if (heroAliasName) heroAliasName.textContent = currentAlias;
            if (localPeerName) localPeerName.textContent = `${currentAlias} (You)`;

            // Always start with counselor banner hidden on page load.
            // The banner is only shown by a live counselor_join_text WS event.
            counselorActive = false;
            const counselorConnectedBannerEarly = document.getElementById("counselor-connected-banner");
            if (counselorConnectedBannerEarly) counselorConnectedBannerEarly.style.display = "none";
            if (heroIntro) heroIntro.style.display = "block";

            // Ensure persistent student WS is connected with the validated session_id
            if (!studentWS || prevSessionId !== sessionId || randomize) {
                initStudentPersistentWS();
            }
        } catch (e) {
            console.error("Auth error:", e);
        }
    }
    initStudentSession(false, true); // isPageLoad=true → always resets counselor state

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
            initCounselorWS();
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
            this.currentPeerAlias = config.peerAlias || (this.mode === 'counselor' ? (activeTargetAlias || "Student") : (this.mode === 'student' ? "Campus Counselor" : null));
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

        async startVoiceCall(isInitiator = true, peerAlias = null) {
            if (peerAlias && peerAlias !== "null" && peerAlias !== "undefined") {
                this.currentPeerAlias = peerAlias;
            }
            if (!this.currentPeerAlias || this.currentPeerAlias === "null" || this.currentPeerAlias === "undefined") {
                this.currentPeerAlias = this.mode === 'counselor' ? (activeTargetAlias || "Student") : (this.mode === 'student' ? "Campus Counselor" : "Anonymous Peer");
            }

            voiceCallOverlay.style.display = "flex";
            this.resetCallUI();
            matchmakingStage.style.display = "flex";
            activePeerStage.style.display = "none";
            matchmakingStatusHeading.textContent = `Connecting to ${this.currentPeerAlias}...`;

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
                await this.initiatePeerConnection(isInitiator !== undefined ? isInitiator : true);
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
            if (!this.currentPeerAlias || this.currentPeerAlias === "null" || this.currentPeerAlias === "undefined") {
                this.currentPeerAlias = this.mode === 'counselor' ? (activeTargetAlias || "Student") : (this.mode === 'student' ? "Campus Counselor" : "Anonymous Peer");
            }

            // Set clear pod titles for participants
            if (this.mode === 'counselor') {
                if (localPeerName) localPeerName.textContent = "You (Counselor)";
                if (remotePeerName) remotePeerName.textContent = this.currentPeerAlias;
            } else if (this.mode === 'student') {
                if (localPeerName) localPeerName.textContent = currentAlias ? `You (${currentAlias})` : "You";
                if (remotePeerName) remotePeerName.textContent = "Campus Counselor";
            } else {
                if (localPeerName) localPeerName.textContent = currentAlias ? `You (${currentAlias})` : "You (Anon)";
                if (remotePeerName) remotePeerName.textContent = this.currentPeerAlias;
            }

            if (this.mode === 'student' && !isInitiator) {
                // Student waiting for counselor to connect
                matchmakingStage.style.display = "flex";
                activePeerStage.style.display = "none";
                callConnectionBadge.textContent = "Waiting for Counselor...";
                callPeerLabel.textContent = `Waiting for ${this.currentPeerAlias} to join...`;
                matchmakingStatusHeading.textContent = `Waiting for ${this.currentPeerAlias} to join voice call...`;
            } else {
                matchmakingStage.style.display = "none";
                activePeerStage.style.display = "flex";
                callLivePill.classList.add("connected");
                callConnectionBadge.textContent = isInitiator ? (this.mode === 'counselor' ? "Calling Student..." : "Connecting...") : "Live 2-Way Voice";
                callPeerLabel.textContent = `Connected with ${this.currentPeerAlias}`;
                remoteActivityLabel.textContent = "Connected";
                this.startTimer();
            }

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

            // Monitor ICE connection state
            this.peerConnection.oniceconnectionstatechange = () => {
                if (this.peerConnection) {
                    const state = this.peerConnection.iceConnectionState;
                    if (state === "disconnected" || state === "failed" || state === "closed") {
                        this.handlePeerLeft("Peer disconnected from voice call");
                    }
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
            try {
                if (!this.peerConnection) {
                    if (!this.localStream) {
                        this.localStream = await navigator.mediaDevices.getUserMedia({
                            audio: {
                                echoCancellation: true,
                                noiseSuppression: true,
                                autoGainControl: true
                            },
                            video: false
                        });
                        this.setupLocalAudioVisualizer(this.localStream);
                    }
                    await this.initiatePeerConnection(false);
                }
                await this.peerConnection.setRemoteDescription(new RTCSessionDescription(offer));
                const answer = await this.peerConnection.createAnswer();
                await this.peerConnection.setLocalDescription(answer);
                this.sendSignal({
                    type: "answer",
                    answer: answer
                });

                // Transition UI to active call
                matchmakingStage.style.display = "none";
                activePeerStage.style.display = "flex";
                callLivePill.classList.add("connected");
                callConnectionBadge.textContent = "Live 2-Way Voice";
                callPeerLabel.textContent = `Connected with ${this.currentPeerAlias}`;
                remotePeerName.textContent = this.currentPeerAlias;
                remoteActivityLabel.textContent = "Connected";
                this.startTimer();
            } catch (e) {
                console.error("Handle offer error:", e);
            }
        }

        async handleRemoteAnswer(answer) {
            if (!this.peerConnection) return;
            try {
                await this.peerConnection.setRemoteDescription(new RTCSessionDescription(answer));
                matchmakingStage.style.display = "none";
                activePeerStage.style.display = "flex";
                callLivePill.classList.add("connected");
                callConnectionBadge.textContent = "Live 2-Way Voice";
                callPeerLabel.textContent = `Connected with ${this.currentPeerAlias}`;
                remoteActivityLabel.textContent = "Connected";
                this.startTimer();
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
            callConnectionBadge.textContent = "Connecting...";
            const peerName = this.currentPeerAlias || (this.mode === 'counselor' ? (activeTargetAlias || "Student") : (this.mode === 'student' ? "Campus Counselor" : "peer"));
            callPeerLabel.textContent = `Connecting with ${peerName}...`;
            localOrbWrapper.className = "peer-orb-wrapper";
            remoteOrbWrapper.className = "peer-orb-wrapper";
            this.isMuted = false;
            callMuteBtn.classList.remove("active-muted");
            muteBtnLabel.textContent = "Mute";

            if (this.mode !== 'peer') {
                if (callNextPeerBtn) callNextPeerBtn.style.display = "none";
                if (callCounselorAlertBtn) callCounselorAlertBtn.style.display = "none";
            } else {
                if (callNextPeerBtn) callNextPeerBtn.style.display = "inline-flex";
                if (callCounselorAlertBtn) callCounselorAlertBtn.style.display = "inline-flex";
            }
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
            if (remotePeerAudio) {
                remotePeerAudio.pause();
                remotePeerAudio.srcObject = null;
            }
            if (this.timerInterval) clearInterval(this.timerInterval);
            if (this.animationFrameId) cancelAnimationFrame(this.animationFrameId);

            if (callNextPeerBtn) callNextPeerBtn.style.display = "inline-flex";
            if (callCounselorAlertBtn) callCounselorAlertBtn.style.display = "inline-flex";

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
                        contactCounselorBtn.textContent = "Counselor Alerted";
                        const heroIntro = document.getElementById("hero-intro");
                        const counselorWaitingBanner = document.getElementById("counselor-waiting-banner");
                        const counselorWaitingText = document.getElementById("counselor-waiting-text");
                        
                        if (heroIntro) heroIntro.style.display = "none";
                        
                        if (counselorWaitingBanner) {
                            counselorWaitingText.textContent = `Waiting for a counselor to join your ${mode} session...`;
                            counselorWaitingBanner.style.display = "flex";
                        }
                        
                        if (mode === "voice") {
                            voiceCallOverlay.style.display = "flex";
                            if (callConnectionBadge) callConnectionBadge.textContent = "Waiting for Counselor...";
                            if (callPeerLabel) callPeerLabel.textContent = "Connecting to Campus Counselor...";
                            if (matchmakingStatusHeading) matchmakingStatusHeading.textContent = "Waiting for Campus Counselor to join voice call...";

                            window.directVoiceChatManager = new PeerVoiceChatManager({
                                mode: 'student',
                                peerAlias: "Campus Counselor",
                                signalSender: (signalData) => {
                                    if (studentWS && studentWS.readyState === WebSocket.OPEN) {
                                        studentWS.send(JSON.stringify(signalData));
                                    }
                                }
                            });
                            await window.directVoiceChatManager.startVoiceCall(false, "Campus Counselor");
                        }
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
    function getActiveVoiceManager() {
        if (window.directVoiceChatManager && (window.directVoiceChatManager.localStream || window.directVoiceChatManager.peerConnection)) {
            return window.directVoiceChatManager;
        }
        return peerVoiceChatManager;
    }

    callMuteBtn.addEventListener("click", () => getActiveVoiceManager().toggleMute());
    callNextPeerBtn.addEventListener("click", () => getActiveVoiceManager().nextPeer());
    callCounselorAlertBtn.addEventListener("click", () => getActiveVoiceManager().alertCounselor());
    endVoiceCallBtn.addEventListener("click", () => {
        getActiveVoiceManager().endVoiceCall();
        if (window.directVoiceChatManager) {
            window.directVoiceChatManager = null;
        }
    });

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

        // 1. If Counselor has intervened / is active in this session, route directly to Counselor
        if (counselorActive) {
            sendCounselorReply(text);
            sendButton.disabled = false;
            return;
        }

        // 2. If student is in P2P Text Chat with a peer
        if (peerTextChatManager && peerTextChatManager.isActive()) {
            peerTextChatManager.sendMessage(text);
            sendButton.disabled = false;
            return;
        }

        // 3. Standard AI CBT Coach Interaction
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
                sendButton.disabled = false;
                appendMessage("coach", "You're typing super fast! Take a breath and wait a few seconds before sending another message.");
                return;
            }

            if (!res.ok) throw new Error("HTTP error " + res.status);

            const data = await res.json();
            setTyping(false);
            sendButton.disabled = false;

            if (data.session_id && SESSION_PATTERN.test(data.session_id)) {
                sessionId = data.session_id;
                localStorage.setItem("peerspace_session_id", sessionId);
            }

            if (data.counselor_active) {
                counselorActive = true;
                sessionStorage.setItem("peerspace_counselor_active_" + sessionId, "true");
                if (counselorConnectedBanner) counselorConnectedBanner.style.display = "flex";
                if (heroIntro) heroIntro.style.display = "none";
                const counselorWaitingBanner = document.getElementById("counselor-waiting-banner");
                if (counselorWaitingBanner) counselorWaitingBanner.style.display = "none";
            }

            if (data.reply) {
                appendMessage("coach", data.reply);
            }

            checkAlertBadge();
        } catch (err) {
            console.error("Chat error:", err);
            setTyping(false);
            sendButton.disabled = false;
            appendMessage("coach", "Hey, my connection dropped for a second. Could you repeat that?");
        }
    }

    function sendCounselorReply(text) {
        const msgId = "msg-" + Date.now() + "-" + Math.random().toString(36).substring(2, 9);
        const payload = {
            type: "chat_reply",
            msg_id: msgId,
            session_id: sessionId,
            alias: currentAlias || "Student",
            message: text
        };

        let wsSent = false;
        if (studentWS && studentWS.readyState === WebSocket.OPEN) {
            try {
                studentWS.send(JSON.stringify(payload));
                wsSent = true;
                console.log("Sent chat_reply via studentWS:", payload);
            } catch (err) {
                console.warn("Failed to send reply via studentWS:", err);
            }
        }

        // Only invoke HTTP fallback when WebSocket is not open or failed
        if (!wsSent) {
            console.warn("studentWS not open. Reconnecting and using HTTP fallback /api/chat/reply...");
            initStudentPersistentWS();

            fetch("/api/chat/reply", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            }).then(res => {
                if (!res.ok) console.warn("Fallback /api/chat/reply HTTP error:", res.status);
            }).catch(err => {
                console.warn("Fallback /api/chat/reply failed:", err);
            });
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

                sessionStorage.removeItem("peerspace_counselor_active_" + sessionId);
                sessionId = generateUUID();
                localStorage.setItem("peerspace_session_id", sessionId);
                counselorActive = false;
                if (counselorConnectedBanner) counselorConnectedBanner.style.display = "none";
                await initStudentSession();
                initStudentPersistentWS();

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
            adminToken = passkey;
            sessionStorage.setItem("peerspace_admin_token", adminToken);

            adminAuthGate.style.display = "none";
            adminMainContent.style.display = "block";
            initCounselorWS();
            loadAdminDashboard();
            alertsPollInterval = setInterval(loadAdminDashboard, 5000);
        } catch (e) {
            alert("Authentication failed.");
        }
    });

    function forceAdminLogout() {
        sessionStorage.removeItem("peerspace_admin_token");
        adminToken = null;
        if (alertsPollInterval) clearInterval(alertsPollInterval);
        if (counselorWS) {
            try {
                counselorWS.onclose = null;
                counselorWS.onerror = null;
                counselorWS.close();
            } catch(e) {}
            counselorWS = null;
        }
        if (counselorWSRetryTimer) {
            clearTimeout(counselorWSRetryTimer);
            counselorWSRetryTimer = null;
        }
        
        adminPasskeyInput.value = "";
        adminAuthGate.style.display = "flex";
        adminMainContent.style.display = "none";
        switchToStudentView();
    }

    if (adminLogoutBtn) {
        adminLogoutBtn.addEventListener("click", () => forceAdminLogout());
    }

    refreshAlertsBtn.addEventListener("click", () => loadAdminDashboard());

    async function loadAdminDashboard() {
        try {
            const alertsRes = await fetch("/api/admin/alerts", {
                headers: { "x-admin-token": adminToken }
            });
            if (alertsRes.status === 401) {
                forceAdminLogout();
                return;
            }
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

            const sessionsRes = await fetch("/api/admin/sessions", {
                headers: { "x-admin-token": adminToken }
            });
            const sessionsData = await sessionsRes.json();
            statActiveSessions.textContent = sessionsData.total_active || 0;
            renderSessions(sessionsData.active_sessions || []);
        } catch (e) {
            console.error("Admin dashboard fetch error:", e);
        }
    }

    async function checkAlertBadge() {
        try {
            const alertsRes = await fetch("/api/admin/alerts", {
                headers: { "x-admin-token": adminToken }
            });
            if (alertsRes.status === 401) {
                forceAdminLogout();
                return;
            }
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
                            <button class="btn-secondary join-counselor-text-btn" data-session-id="${alert.session_id}" data-alias="${escapeHtml(alert.alias || '')}" data-alert-id="${alert.id}" style="padding: 0.5rem 1rem; border-radius: 4px; border: 1px solid var(--border-color); background: var(--bg-card); cursor: pointer; color: var(--text-color);">Join Text Chat</button>
                            <button class="btn-secondary join-counselor-voice-btn" data-session-id="${alert.session_id}" data-alias="${escapeHtml(alert.alias || '')}" data-alert-id="${alert.id}" style="padding: 0.5rem 1rem; border-radius: 4px; border: 1px solid var(--border-color); background: var(--bg-card); cursor: pointer; color: var(--text-color); margin-left: 0.5rem;">Join Voice Call</button>
                          `
                        : `<span class="alert-status-badge ${alert.status}">Status: ${alert.status}</span>
                           <button class="btn-secondary join-counselor-text-btn" data-session-id="${alert.session_id}" data-alias="${escapeHtml(alert.alias || '')}" data-alert-id="${alert.id}" style="margin-left: 1rem; padding: 0.5rem 1rem; border-radius: 4px; border: 1px solid var(--border-color); background: var(--bg-card); cursor: pointer; color: var(--text-color);">Join Text Chat</button>
                           <button class="btn-secondary join-counselor-voice-btn" data-session-id="${alert.session_id}" data-alias="${escapeHtml(alert.alias || '')}" data-alert-id="${alert.id}" style="margin-left: 0.5rem; padding: 0.5rem 1rem; border-radius: 4px; border: 1px solid var(--border-color); background: var(--bg-card); cursor: pointer; color: var(--text-color);">Join Voice Call</button>`
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

            card.querySelectorAll(".join-counselor-text-btn").forEach((btn) => {
                btn.addEventListener("click", async () => {
                    const sid = btn.getAttribute("data-session-id");
                    const alias = btn.getAttribute("data-alias");
                    const alertId = btn.getAttribute("data-alert-id");
                    
                    if (alert.status === "PENDING") {
                        await dispatchAlertAction(alertId, "DISPATCHED");
                    }
                    
                    openCounselorChat(sid, alias);
                });
            });

            card.querySelectorAll(".join-counselor-voice-btn").forEach((btn) => {
                btn.addEventListener("click", async () => {
                    const sid = btn.getAttribute("data-session-id");
                    const alias = btn.getAttribute("data-alias");
                    const alertId = btn.getAttribute("data-alert-id");
                    
                    if (alert.status === "PENDING") {
                        await dispatchAlertAction(alertId, "DISPATCHED");
                    }
                    
                    await openCounselorVoiceCall(sid, alias);
                });
            });

            alertsFeed.appendChild(card);
        });
    }

    async function dispatchAlertAction(alertId, action) {
        try {
            const res = await fetch(`/api/admin/alerts/${alertId}/action`, {
                method: "POST",
                headers: { 
                    "Content-Type": "application/json",
                    "x-admin-token": adminToken
                },
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
            const reasoningTag = s.has_reasoning
                ? `<span class="pastel-badge blue" style="font-size: 0.65rem; margin-left: 0.4rem; padding: 0.15rem 0.45rem; vertical-align: middle;" title="${escapeHtml(s.reasoning_preview || 'AI Reasoning active')}">AI Analyzed</span>`
                : '';
            tr.innerHTML = `
                <td><strong>${escapeHtml(s.alias)}</strong>${reasoningTag}</td>
                <td><code>${s.session_id}</code></td>
                <td>${s.messages} msg(s)</td>
                <td>${s.last_active}</td>
                <td>
                    <button class="btn-secondary join-counselor-chat-btn" data-id="${s.full_id}" style="padding: 0.3rem 0.8rem; font-size: 0.8rem;">Text Chat</button>
                    <button class="btn-secondary join-counselor-voice-row-btn" data-id="${s.full_id}" style="margin-left: 0.4rem; padding: 0.3rem 0.8rem; font-size: 0.8rem;">Voice Call</button>
                </td>
            `;
            tr.querySelector('.join-counselor-chat-btn').addEventListener('click', () => {
                openCounselorChat(s.full_id, s.alias);
            });
            tr.querySelector('.join-counselor-voice-row-btn').addEventListener('click', () => {
                openCounselorVoiceCall(s.full_id, s.alias);
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

    const counselorConnectedBanner = document.getElementById("counselor-connected-banner");
    if (counselorActive && counselorConnectedBanner) {
        counselorConnectedBanner.style.display = "flex";
        if (heroIntro) heroIntro.style.display = "none";
    }

    const dismissCounselorBannerBtn = document.getElementById("dismiss-counselor-banner-btn");
    if (dismissCounselorBannerBtn) {
        dismissCounselorBannerBtn.addEventListener("click", async () => {
            counselorActive = false;
            sessionStorage.removeItem("peerspace_counselor_active_" + sessionId);
            if (counselorConnectedBanner) counselorConnectedBanner.style.display = "none";
            if (heroIntro) heroIntro.style.display = "block";
            try {
                await fetch("/api/reset", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ session_id: sessionId })
                });
            } catch (e) {}
        });
    }

    const brandElement = document.querySelector(".brand");
    if (brandElement) {
        brandElement.style.cursor = "pointer";
        brandElement.addEventListener("click", () => {
            switchToStudentView();
            if (heroIntro) heroIntro.style.display = "block";
        });
    }

    function initStudentPersistentWS() {
        if (studentWSRetryTimer) {
            clearTimeout(studentWSRetryTimer);
            studentWSRetryTimer = null;
        }

        if (studentWS) {
            try {
                studentWS.onclose = null;
                studentWS.onerror = null;
                studentWS.close();
            } catch (e) {}
        }

        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        studentWS = new WebSocket(`${protocol}//${window.location.host}/ws/student?session_id=${encodeURIComponent(sessionId)}`);
        
        studentWS.onopen = () => {
            console.log("studentWS connected for session:", sessionId);
        };

        studentWS.onclose = (e) => {
            console.warn("studentWS disconnected. Scheduling reconnect in 2s...", e.code);
            studentWSRetryTimer = setTimeout(initStudentPersistentWS, 2000);
        };

        studentWS.onerror = (e) => {
            console.error("studentWS error:", e);
        };

        studentWS.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === "counselor_join_text") {
                counselorActive = true;
                sessionStorage.setItem("peerspace_counselor_active_" + sessionId, "true");
                if (voiceCallOverlay && voiceCallOverlay.style.display === "flex") {
                    if (typeof getActiveVoiceManager === 'function') getActiveVoiceManager().endVoiceCall();
                }
                if (counselorConnectedBanner) counselorConnectedBanner.style.display = "flex";
                if (heroIntro) heroIntro.style.display = "none";
                const counselorWaitingBanner = document.getElementById("counselor-waiting-banner");
                if (counselorWaitingBanner) counselorWaitingBanner.style.display = "none";
                
                appendMessage("coach", "A campus counselor has joined your session. Responses are now from a human professional.", "Live Counselor");
            } else if (data.type === "counselor_join_voice") {
                // Counselor clicked "Join Voice Call" — prepare the student side to receive the WebRTC offer
                const counselorWaitingBanner = document.getElementById("counselor-waiting-banner");
                if (counselorWaitingBanner) counselorWaitingBanner.style.display = "none";
                if (heroIntro) heroIntro.style.display = "none";
                
                // Open voice overlay in "waiting" mode
                voiceCallOverlay.style.display = "flex";
                if (matchmakingStage) matchmakingStage.style.display = "flex";
                if (activePeerStage) activePeerStage.style.display = "none";
                if (callConnectionBadge) callConnectionBadge.textContent = "Counselor Joining...";
                if (callPeerLabel) callPeerLabel.textContent = "Campus Counselor is joining your voice session...";
                if (matchmakingStatusHeading) matchmakingStatusHeading.textContent = "Campus Counselor is connecting...";

                // Prepare student voice manager to receive the WebRTC offer
                if (!window.directVoiceChatManager) {
                    window.directVoiceChatManager = new PeerVoiceChatManager({
                        mode: 'student',
                        peerAlias: "Campus Counselor",
                        signalSender: (signalData) => {
                            if (studentWS && studentWS.readyState === WebSocket.OPEN) {
                                studentWS.send(JSON.stringify(signalData));
                            }
                        }
                    });
                    // Get microphone access in advance so there's no delay when offer arrives
                    (async () => {
                        try {
                            window.directVoiceChatManager.localStream = await navigator.mediaDevices.getUserMedia({
                                audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
                                video: false
                            });
                            window.directVoiceChatManager.setupLocalAudioVisualizer(window.directVoiceChatManager.localStream);
                        } catch (err) {
                            console.warn("Mic access error:", err);
                        }
                    })();
                }
            } else if (data.type === "counselor_chat" || data.type === "counselor_message") {
                counselorActive = true;
                sessionStorage.setItem("peerspace_counselor_active_" + sessionId, "true");
                if (counselorConnectedBanner) counselorConnectedBanner.style.display = "flex";
                if (heroIntro) heroIntro.style.display = "none";
                const counselorWaitingBanner = document.getElementById("counselor-waiting-banner");
                if (counselorWaitingBanner) counselorWaitingBanner.style.display = "none";
                
                appendMessage("coach", data.message, "Human Counselor");
            } else if (data.type === "counselor_leave_text") {
                counselorActive = false;
                sessionStorage.removeItem("peerspace_counselor_active_" + sessionId);
                if (counselorConnectedBanner) counselorConnectedBanner.style.display = "none";
                appendMessage("coach", "Counselor has ended the live intervention. You are back with your AI CBT coach.", "System");
            } else if (data.type === "counselor_voice_invite") {
                const inviteBanner = document.getElementById("counselor-voice-invite-banner");
                if (inviteBanner) {
                    inviteBanner.style.display = "flex";
                    document.getElementById("accept-counselor-call-btn").onclick = async () => {
                        inviteBanner.style.display = "none";
                        const peerName = "Campus Counselor";
                        window.directVoiceChatManager = new PeerVoiceChatManager({
                            mode: 'student',
                            peerAlias: peerName,
                            signalSender: (signalData) => {
                                if (studentWS && studentWS.readyState === WebSocket.OPEN) {
                                    studentWS.send(JSON.stringify(signalData));
                                }
                            }
                        });
                        await window.directVoiceChatManager.startVoiceCall(false, peerName);
                        studentWS.send(JSON.stringify({ type: "student_voice_accept" }));
                    };
                    document.getElementById("decline-counselor-call-btn").onclick = () => {
                        inviteBanner.style.display = "none";
                        studentWS.send(JSON.stringify({ type: "student_voice_decline" }));
                    };
                }
            } else if (data.type === "counselor_webrtc_signal") {
                const counselorWaitingBanner = document.getElementById("counselor-waiting-banner");
                if (counselorWaitingBanner) counselorWaitingBanner.style.display = "none";
                if (!window.directVoiceChatManager) {
                    window.directVoiceChatManager = new PeerVoiceChatManager({
                        mode: 'student',
                        peerAlias: "Campus Counselor",
                        signalSender: (signalData) => {
                            if (studentWS && studentWS.readyState === WebSocket.OPEN) {
                                studentWS.send(JSON.stringify(signalData));
                            }
                        }
                    });
                    voiceCallOverlay.style.display = "flex";
                }
                window.directVoiceChatManager.handleSignalingMessage(data.signal);
            }
        };
    }
    
    initStudentPersistentWS();

    if (studentAliasBadge) {
        studentAliasBadge.addEventListener("click", () => {
            setTimeout(initStudentPersistentWS, 400); 
        });
    }

    const counselorChatPanel = document.getElementById("counselor-chat-panel");
    const closeCounselorChatBtn = document.getElementById("close-counselor-chat-btn");
    const counselorChatMessages = document.getElementById("counselor-chat-messages");
    const counselorChatForm = document.getElementById("counselor-chat-form");
    const counselorMessageInput = document.getElementById("counselor-message-input");
    const counselorStartCallBtn = document.getElementById("counselor-start-call-btn");

    const counselorSeenMsgKeys = new Set();

    if (counselorStartCallBtn) {
        counselorStartCallBtn.addEventListener("click", async () => {
            if (!activeTargetSessionId) return;
            await openCounselorVoiceCall(activeTargetSessionId, activeTargetAlias);
        });
    }

    function initCounselorWS() {
        if (!adminToken) return;

        if (counselorWSRetryTimer) {
            clearTimeout(counselorWSRetryTimer);
            counselorWSRetryTimer = null;
        }

        if (counselorWS) {
            try {
                counselorWS.onclose = null;
                counselorWS.onerror = null;
                counselorWS.close();
            } catch (e) {}
        }

        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        counselorWS = new WebSocket(`${protocol}//${window.location.host}/ws/counselor?token=${encodeURIComponent(adminToken)}`);
        
        counselorWS.onopen = () => {
            console.log("counselorWS connected to server.");
        };

        counselorWS.onclose = (e) => {
            console.warn("counselorWS closed:", e.code);
            if (e.code === 1008) {
                forceAdminLogout();
            } else if (adminToken) {
                counselorWSRetryTimer = setTimeout(initCounselorWS, 2000);
            }
        };

        counselorWS.onerror = (e) => {
            console.error("counselorWS error:", e);
        };

        counselorWS.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === "student_chat_reply") {
                const incomingSid = String(data.session_id || "").trim();
                const activeSid = String(activeTargetSessionId || "").trim();
                const senderAlias = data.alias || "Student";
                const msgKey = data.msg_id || `${incomingSid}:${data.message}`;

                // Deduplicate: suppress double-rendering if multiple network transports arrive
                if (counselorSeenMsgKeys.has(msgKey)) {
                    console.log("[Counselor] Suppressed duplicate student message:", msgKey);
                    return;
                }
                counselorSeenMsgKeys.add(msgKey);
                setTimeout(() => counselorSeenMsgKeys.delete(msgKey), 15000);

                console.log(`[Counselor] student_chat_reply from ${senderAlias} (${incomingSid}):`, data.message);

                const isChatOpen = counselorChatPanel && counselorChatPanel.style.display !== "none";
                const sidMatches = activeSid && (
                    incomingSid === activeSid ||
                    incomingSid.toLowerCase() === activeSid.toLowerCase() ||
                    incomingSid.startsWith(activeSid.substring(0, 8)) ||
                    activeSid.startsWith(incomingSid.substring(0, 8))
                );

                if (sidMatches || (isChatOpen && (!activeSid || activeSid === "anon-session"))) {
                    // Update active target session ID if not set or was prefix
                    if (!activeTargetSessionId || activeTargetSessionId === "anon-session") {
                        activeTargetSessionId = incomingSid;
                    }
                    if (senderAlias && senderAlias !== "Student") {
                        activeTargetAlias = senderAlias;
                    }
                    if (counselorChatMessages) {
                        const emptyFeed = counselorChatMessages.querySelector(".empty-feed-text");
                        if (emptyFeed) emptyFeed.remove();

                        const msgEl = document.createElement("div");
                        msgEl.className = "message ai-message";
                        msgEl.innerHTML = `
                            <div class="message-content" style="border-left: 3px solid #10b981;">
                                <strong style="display:block; margin-bottom: 0.2rem; font-size: 0.8rem; color: var(--text-muted);">${escapeHtml(senderAlias)}</strong>
                                ${escapeHtml(data.message).replace(/\n/g, '<br/>')}
                            </div>
                        `;
                        counselorChatMessages.appendChild(msgEl);
                        counselorChatMessages.scrollTop = counselorChatMessages.scrollHeight;
                    }
                } else {
                    // Update dashboard count or table if message belongs to another student
                    loadAdminDashboard();
                }
            } else if (data.type === "agent_reasoning") {
                const incomingSid = String(data.session_id || "").trim();
                const activeSid = String(activeTargetSessionId || "").trim();
                const sidMatches = activeSid && (
                    incomingSid === activeSid ||
                    incomingSid.toLowerCase() === activeSid.toLowerCase() ||
                    incomingSid.startsWith(activeSid.substring(0, 8)) ||
                    activeSid.startsWith(incomingSid.substring(0, 8))
                );

                if (sidMatches && counselorChatMessages) {
                    const emptyFeed = counselorChatMessages.querySelector(".empty-feed-text");
                    if (emptyFeed) emptyFeed.remove();

                    const reasoningEl = document.createElement("div");
                    reasoningEl.className = "message reasoning-event";
                    reasoningEl.innerHTML = `
                        <div class="message-content" style="border-left: 3px solid #1F6C9F; background: rgba(31, 108, 159, 0.08); padding: 0.65rem 0.85rem; border-radius: 6px; margin: 0.5rem 0;">
                            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.35rem;">
                                <span class="pastel-badge blue" style="font-size: 0.7rem; letter-spacing: 0.05em; text-transform: uppercase;">Live AI Reasoning Analysis</span>
                                <span style="font-size: 0.72rem; color: var(--text-muted); font-family: var(--font-mono, monospace);">${escapeHtml(data.timestamp || "")}</span>
                            </div>
                            <div style="font-size: 0.82rem; color: var(--text-secondary); line-height: 1.45; font-family: var(--font-mono, monospace);">
                                ${escapeHtml(data.reasoning).replace(/\n/g, '<br/>')}
                            </div>
                        </div>
                    `;
                    counselorChatMessages.appendChild(reasoningEl);
                    counselorChatMessages.scrollTop = counselorChatMessages.scrollHeight;
                }
            } else if (data.type === "new_alert") {
                loadAdminDashboard();
            } else if (data.type === "student_webrtc_signal") {
                const incomingSid = String(data.session_id || "").trim();
                const activeSid = String(activeTargetSessionId || "").trim();
                const sidMatches = !activeSid || incomingSid === activeSid || incomingSid.startsWith(activeSid.substring(0, 8)) || activeSid.startsWith(incomingSid.substring(0, 8));
                if (sidMatches && window.directVoiceChatManager) {
                    window.directVoiceChatManager.handleSignalingMessage(data.signal);
                }
            } else if (data.type === "student_voice_accept" && String(data.session_id).trim() === String(activeTargetSessionId).trim()) {
                if (counselorStartCallBtn) {
                    counselorStartCallBtn.innerHTML = "Connected";
                }
                const peerName = activeTargetAlias || "Student";
                window.directVoiceChatManager = new PeerVoiceChatManager({
                    mode: 'counselor',
                    peerAlias: peerName,
                    signalSender: (signalData) => {
                        signalData.session_id = activeTargetSessionId;
                        if (counselorWS && counselorWS.readyState === WebSocket.OPEN) {
                            counselorWS.send(JSON.stringify(signalData));
                        }
                    }
                });
                window.directVoiceChatManager.startVoiceCall(true, peerName);
            } else if (data.type === "student_voice_decline" && String(data.session_id).trim() === String(activeTargetSessionId).trim()) {
                if (counselorStartCallBtn) {
                    counselorStartCallBtn.innerHTML = "Call Declined";
                    setTimeout(() => {
                        counselorStartCallBtn.innerHTML = "Start Voice Call";
                        counselorStartCallBtn.disabled = false;
                    }, 3000);
                }
            }
        };
    }

    async function loadSessionTranscript(targetSessionId) {
        if (!adminToken || !targetSessionId) return;
        try {
            const res = await fetch(`/api/admin/sessions/${encodeURIComponent(targetSessionId)}/transcript`, {
                headers: { "x-admin-token": adminToken }
            });
            if (!res.ok) return;
            const data = await res.json();
            if (counselorChatMessages) {
                counselorChatMessages.innerHTML = "";

                if (data.last_reasoning) {
                    const reasoningCard = document.createElement("div");
                    reasoningCard.className = "message reasoning-banner";
                    reasoningCard.innerHTML = `
                        <div class="message-content" style="border-left: 3px solid #1F6C9F; background: rgba(31, 108, 159, 0.08); padding: 0.65rem 0.85rem; border-radius: 6px; margin-bottom: 0.75rem;">
                            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.35rem;">
                                <span class="pastel-badge blue" style="font-size: 0.7rem; letter-spacing: 0.05em; text-transform: uppercase;">Latest AI Reasoning & Cognitive Analysis</span>
                                <span style="font-size: 0.72rem; color: var(--text-muted); font-family: var(--font-mono, monospace);">Analyzes Info & Decides Action</span>
                            </div>
                            <div style="font-size: 0.82rem; color: var(--text-secondary); line-height: 1.45; font-family: var(--font-mono, monospace);">
                                ${escapeHtml(data.last_reasoning).replace(/\n/g, '<br/>')}
                            </div>
                        </div>
                    `;
                    counselorChatMessages.appendChild(reasoningCard);
                }

                if (data.transcript && data.transcript.length > 0) {
                    data.transcript.forEach(t => {
                        const msgEl = document.createElement("div");
                        const isUser = t.role === "user";
                        const isCounselor = t.sender === "Counselor";
                        const isCoach = t.sender === "AI Coach";

                        if (isCounselor) {
                            msgEl.className = "message user-message";
                            msgEl.innerHTML = `
                                <div class="message-content">
                                    <strong style="display:block; margin-bottom: 0.2rem; font-size: 0.8rem; opacity: 0.8;">Counselor (You)</strong>
                                    ${escapeHtml(t.content).replace(/\n/g, '<br/>')}
                                </div>
                            `;
                        } else if (isUser) {
                            msgEl.className = "message ai-message";
                            msgEl.innerHTML = `
                                <div class="message-content" style="border-left: 3px solid #10b981;">
                                    <strong style="display:block; margin-bottom: 0.2rem; font-size: 0.8rem; color: var(--text-muted);">${escapeHtml(t.sender || "Student")}</strong>
                                    ${escapeHtml(t.content).replace(/\n/g, '<br/>')}
                                </div>
                            `;
                        } else if (isCoach) {
                            msgEl.className = "message";
                            msgEl.innerHTML = `
                                <div class="message-content" style="border-left: 3px solid #3b82f6; background: rgba(59, 130, 246, 0.08); padding: 0.6rem 0.8rem; border-radius: 8px; margin-bottom: 0.5rem;">
                                    <strong style="display:block; margin-bottom: 0.2rem; font-size: 0.8rem; color: #3b82f6;">AI Coach (Past Turn)</strong>
                                    <span style="font-size: 0.88rem; color: var(--text-main);">${escapeHtml(t.content).replace(/\n/g, '<br/>')}</span>
                                </div>
                            `;
                        } else {
                            msgEl.className = "message";
                            msgEl.innerHTML = `
                                <div style="text-align: center; font-size: 0.75rem; color: var(--text-muted); margin: 0.4rem 0;">
                                    <em>${escapeHtml(t.content)}</em>
                                </div>
                            `;
                        }
                        counselorChatMessages.appendChild(msgEl);
                    });
                    counselorChatMessages.scrollTop = counselorChatMessages.scrollHeight;
                }
            }
        } catch (e) {
            console.error("Failed to load session transcript:", e);
        }
    }

    function openCounselorChat(targetSessionId, targetAlias = null) {
        activeTargetSessionId = String(targetSessionId).trim();
        activeTargetAlias = targetAlias ? String(targetAlias).trim() : null;
        if (!counselorWS || counselorWS.readyState !== WebSocket.OPEN) {
            initCounselorWS();
        }
        
        const titleEl = document.getElementById("counselor-chat-title");
        if (titleEl) {
            const displayName = activeTargetAlias || (activeTargetSessionId.length > 12 ? activeTargetSessionId.substring(0, 8) + '...' : activeTargetSessionId);
            titleEl.textContent = `Live Session with ${displayName}`;
        }

        const sendJoinNotification = () => {
            if (counselorWS && counselorWS.readyState === WebSocket.OPEN) {
                counselorWS.send(JSON.stringify({ type: "counselor_join_text", session_id: activeTargetSessionId }));
            }
        };

        if (counselorWS && counselorWS.readyState === WebSocket.OPEN) {
            sendJoinNotification();
        } else {
            setTimeout(sendJoinNotification, 500);
        }

        if (counselorChatPanel) counselorChatPanel.style.display = "block";
        if (counselorChatMessages) {
            counselorChatMessages.innerHTML = '<div class="empty-feed-text">Loading student session history...</div>';
            counselorChatMessages.style.display = "flex";
            counselorChatMessages.style.flexDirection = "column";
        }
        loadSessionTranscript(activeTargetSessionId);
        if (counselorChatPanel) counselorChatPanel.scrollIntoView({ behavior: 'smooth' });
    }

    async function openCounselorVoiceCall(targetSessionId, targetAlias = null) {
        activeTargetSessionId = String(targetSessionId).trim();
        activeTargetAlias = targetAlias ? String(targetAlias).trim() : "Student";

        if (!counselorWS || counselorWS.readyState !== WebSocket.OPEN) {
            initCounselorWS();
        }

        const sendJoinVoice = () => {
            if (counselorWS && counselorWS.readyState === WebSocket.OPEN) {
                counselorWS.send(JSON.stringify({
                    type: "counselor_voice_join",
                    session_id: activeTargetSessionId
                }));
            }
        };

        if (counselorWS && counselorWS.readyState === WebSocket.OPEN) {
            sendJoinVoice();
        } else {
            setTimeout(sendJoinVoice, 400);
        }

        // Close counselor text chat panel if open so it doesn't clash
        if (counselorChatPanel) {
            counselorChatPanel.style.display = "none";
        }

        // Display voice call overlay directly
        voiceCallOverlay.style.display = "flex";
        if (localPeerName) localPeerName.textContent = "You (Counselor)";
        if (remotePeerName) remotePeerName.textContent = activeTargetAlias;
        if (callPeerLabel) callPeerLabel.textContent = `Connecting with ${activeTargetAlias}...`;
        if (callConnectionBadge) callConnectionBadge.textContent = "Calling Student...";

        window.directVoiceChatManager = new PeerVoiceChatManager({
            mode: 'counselor',
            peerAlias: activeTargetAlias,
            signalSender: (signalData) => {
                signalData.session_id = activeTargetSessionId;
                if (counselorWS && counselorWS.readyState === WebSocket.OPEN) {
                    counselorWS.send(JSON.stringify(signalData));
                }
            }
        });

        await window.directVoiceChatManager.startVoiceCall(true, activeTargetAlias);
    }

    if (closeCounselorChatBtn) {
        closeCounselorChatBtn.addEventListener("click", () => {
            if (counselorWS && counselorWS.readyState === WebSocket.OPEN && activeTargetSessionId) {
                counselorWS.send(JSON.stringify({
                    type: "counselor_leave_text",
                    session_id: activeTargetSessionId
                }));
            }
            counselorChatPanel.style.display = "none";
            activeTargetSessionId = null;
            activeTargetAlias = null;
        });
    }

    if (counselorChatForm) {
        counselorChatForm.addEventListener("submit", (e) => {
            e.preventDefault();
            const msg = counselorMessageInput.value.trim();
            if (!msg || !activeTargetSessionId || !counselorWS) return;
            
            const emptyFeed = counselorChatMessages.querySelector(".empty-feed-text");
            if (emptyFeed) emptyFeed.remove();

            const msgEl = document.createElement("div");
            msgEl.className = "message user-message";
            msgEl.innerHTML = `
                <div class="message-content">
                    <strong style="display:block; margin-bottom: 0.2rem; font-size: 0.8rem; opacity: 0.8;">You</strong>
                    ${escapeHtml(msg).replace(/\n/g, '<br/>')}
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
