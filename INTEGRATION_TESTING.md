# Manual Frontend-Backend Integration Testing Checklist

## Overview
This checklist ensures all frontend-backend integrations are working correctly before deployment.

## Prerequisites
- [ ] Backend running on `http://localhost:8000`
- [ ] Frontend running on `http://localhost:5173` or `http://localhost:3000`
- [ ] Browser DevTools open for network inspection

---

## 1. WebSocket Event Stream UI

### Test Scenario: Real-time Event Streaming
**Endpoint**: `/events/ws`

**Steps**:
1. [ ] Open frontend dashboard
2. [ ] Navigate to "Events" or "Live Feed" section
3. [ ] Verify WebSocket connection established (check DevTools → Network → WS)
4. [ ] Trigger backend event (e.g., download model, start job)
5. [ ] Verify event appears in real-time on frontend
6. [ ] Check event data structure matches expected format
7. [ ] Test reconnection after network interruption

**Expected Results**:
- WebSocket connection shows "101 Switching Protocols"
- Events appear within 100ms of backend emission
- No duplicate events
- Clean reconnection on disconnect

---

## 2. Permissions UI

### Test Scenario: Permission Management
**Endpoints**: `/permissions`, `/permissions/grant`, `/permissions/revoke`

**Steps**:
1. [ ] Open permissions management page
2. [ ] Verify all available permissions are listed
3. [ ] Grant a permission (e.g., "camera")
   - [ ] Verify API call succeeds (200 OK)
   - [ ] Verify UI updates immediately
4. [ ] Revoke the same permission
   - [ ] Verify API call succeeds (200 OK)
   - [ ] Verify UI reflects revoked state
5. [ ] Test invalid permission handling
   - [ ] Attempt to grant "invalid_perm"
   - [ ] Verify error message displayed (400 Bad Request)

**Expected Results**:
- Permission list loads correctly
- Grant/revoke operations update UI instantly
- Error messages are user-friendly
- Permission state persists across page refreshes

---

## 3. Model Manager UI

### Test Scenario: Model Download and Management
**Endpoints**: `/models`, `/models/download`, `/jobs/{job_id}`

**Steps**:
1. [ ] Open Model Manager page
2. [ ] Verify model list loads (`GET /models`)
3. [ ] Initiate model download
   - [ ] Select a model (e.g., "phi-3-mini")
   - [ ] Click "Download"
   - [ ] Verify job created (returns `job_id`)
4. [ ] Monitor download progress
   - [ ] Poll `/jobs/{job_id}` for status
   - [ ] Verify progress bar updates
   - [ ] Check for completion notification
5. [ ] Test model deletion
   - [ ] Select downloaded model
   - [ ] Click "Delete"
   - [ ] Verify confirmation dialog
   - [ ] Confirm deletion
   - [ ] Verify model removed from list

**Expected Results**:
- Model list displays correctly
- Download progress updates smoothly
- Job status transitions: pending → running → completed
- Deletion removes model from cache

---

## 4. Chat Interface

### Test Scenario: Conversational AI
**Endpoint**: `/chat`

**Steps**:
1. [ ] Open chat interface
2. [ ] Send a message: "Hello, Lyra!"
   - [ ] Verify message appears in chat
   - [ ] Verify loading indicator shows
3. [ ] Receive response
   - [ ] Verify response appears within 5 seconds
   - [ ] Check response formatting (markdown, code blocks)
4. [ ] Test conversation context
   - [ ] Send follow-up message
   - [ ] Verify context is maintained
5. [ ] Test error handling
   - [ ] Disconnect backend
   - [ ] Send message
   - [ ] Verify error message displayed

**Expected Results**:
- Messages send/receive successfully
- Conversation history preserved
- Graceful error handling
- Markdown rendering works

---

## 5. Status Dashboard

### Test Scenario: System Monitoring
**Endpoint**: `/status`

**Steps**:
1. [ ] Open status dashboard
2. [ ] Verify all metrics display:
   - [ ] CPU usage
   - [ ] RAM usage
   - [ ] GPU status (if available)
   - [ ] Cache usage
   - [ ] Uptime
3. [ ] Check warnings section
   - [ ] Trigger high CPU (run intensive task)
   - [ ] Verify warning appears
4. [ ] Check fallback counters
   - [ ] Verify counters display (even if zero)
5. [ ] Check cache insights
   - [ ] Verify cache size, capacity, hit ratio
6. [ ] Test auto-refresh
   - [ ] Verify dashboard updates every 5-10 seconds

**Expected Results**:
- All metrics display correctly
- Warnings appear when thresholds exceeded
- Dashboard auto-refreshes
- Data visualization is clear

---

## 6. Worker Logs Visualizer

### Test Scenario: Log Streaming
**Endpoint**: Custom log endpoint or file access

**Steps**:
1. [ ] Open logs viewer
2. [ ] Verify recent logs display
3. [ ] Test log filtering
   - [ ] Filter by level (INFO, WARNING, ERROR)
   - [ ] Filter by component
4. [ ] Test log search
   - [ ] Search for specific term
   - [ ] Verify results highlighted
5. [ ] Test real-time updates
   - [ ] Trigger backend action
   - [ ] Verify new logs appear automatically

**Expected Results**:
- Logs display in chronological order
- Filtering works correctly
- Search is fast and accurate
- Real-time updates work

---

## Cross-Cutting Concerns

### CORS Verification
- [ ] All API calls succeed from frontend origin
- [ ] No CORS errors in browser console
- [ ] Preflight requests (OPTIONS) handled correctly

### Authentication (if implemented)
- [ ] Login flow works
- [ ] Protected routes redirect to login
- [ ] Logout clears session
- [ ] Token refresh works

### Error Handling
- [ ] Network errors display user-friendly messages
- [ ] 404 errors handled gracefully
- [ ] 500 errors show generic message (not stack trace)
- [ ] Validation errors highlight specific fields

### Performance
- [ ] Initial page load < 3 seconds
- [ ] API responses < 500ms (p95)
- [ ] WebSocket latency < 100ms
- [ ] No memory leaks (check DevTools → Memory)

### Accessibility
- [ ] Keyboard navigation works
- [ ] Screen reader compatible
- [ ] Color contrast meets WCAG AA
- [ ] Focus indicators visible

---

## Sign-off

**Tested by**: ___________________  
**Date**: ___________________  
**Environment**: ___________________  
**Notes**: ___________________

---

## Known Issues

Document any issues found during testing:

| Issue | Severity | Status | Notes |
|-------|----------|--------|-------|
|       |          |        |       |
