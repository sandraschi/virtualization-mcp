# FastMCP 2.11 Stateful Features

## Table of Contents
1. [Introduction](#introduction)
2. [Key Concepts](#key-concepts)
   - [Sessions](#sessions)
   - [Connection Pooling](#connection-pooling)
   - [Time-To-Live (TTL)](#time-to-live-ttl)
3. [Implementation Details](#implementation-details)
   - [Session Management](#session-management)
   - [Stateful Tools](#stateful-tools)
   - [Connection Pooling](#connection-pooling-implementation)
4. [Usage Examples](#usage-examples)
   - [Creating Stateful Tools](#creating-stateful-tools)
   - [Managing Sessions](#managing-sessions)
   - [Connection Pooling](#using-connection-pooling)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)
7. [Performance Considerations](#performance-considerations)

## Introduction

FastMCP 2.11 introduces stateful features that enable persistent connections and session management, which is particularly useful for VM operations that require maintaining state across multiple requests. This document provides a comprehensive guide to implementing and using these features in virtualization-mcp.

## Key Concepts

### Sessions

Sessions maintain state across multiple requests, allowing tools to store and retrieve data specific to a user or operation. Each session has a unique ID and a configurable TTL (Time-To-Live).

### Connection Pooling

Connection pooling manages a pool of reusable VM connections, reducing the overhead of establishing new connections for each request. Connections are automatically managed based on usage patterns and TTL settings.

### Time-To-Live (TTL)

TTL determines how long sessions and connections remain active without activity. After the TTL period expires, inactive sessions and connections are automatically cleaned up.

## Implementation Details

### Session Management

Sessions are managed by the `SessionManager` class, which handles creation, retrieval, and cleanup of sessions.

```python
from fastmcp.state import SessionManager

# Initialize session manager with 1-hour TTL and 5-minute cleanup interval
session_manager = SessionManager(
    ttl=3600,          # 1 hour session TTL
    cleanup_interval=300  # Clean up expired sessions every 5 minutes
)

# Get or create a session
session = session_manager.get_or_create(session_id)

# Store data in session
session['last_operation'] = 'vm_start'
session['vm_id'] = 'vm-123'

# Get session by ID
session = session_manager.get(session_id)
```

### Stateful Tools

Stateful tools maintain context across multiple invocations using sessions.

```python
from virtualization-mcp.decorators import stateful_tool

@stateful_tool(ttl_seconds=1800)  # 30-minute TTL for this tool's session
async def manage_vm(session, vm_id: str, action: str):
    if 'vm_state' not in session:
        session['vm_state'] = 'initialized'
    
    if action == 'start':
        session['vm_state'] = 'running'
    elif action == 'stop':
        session['vm_state'] = 'stopped'
    
    return {
        'vm_id': vm_id,
        'state': session['vm_state'],
        'session_ttl': session.ttl_remaining
    }
```

### Connection Pooling Implementation

Connection pooling is handled by the `ConnectionPool` class, which manages VM connections efficiently.

```python
from virtualization-mcp.connection import ConnectionPool

# Initialize connection pool
connection_pool = ConnectionPool(
    max_size=20,    # Maximum number of connections to keep in the pool
    ttl=300,        # 5 minutes TTL for idle connections
    max_usage=100   # Maximum number of uses per connection before recycling
)

# Get a connection
connection = await connection_pool.get_connection(vm_id)
try:
    # Use the connection
    result = await connection.execute_command('vm_info')
finally:
    # Return connection to pool
    await connection_pool.release_connection(vm_id, connection)
```

## Usage Examples

### Creating Stateful Tools

```python
from virtualization-mcp.decorators import stateful_tool

@stateful_tool(ttl_seconds=3600)
async def vm_workflow(session, vm_id: str, command: str):
    """Example stateful tool for VM workflow management."""
    # Initialize session state if it doesn't exist
    if 'command_history' not in session:
        session['command_history'] = []
    
    # Update session state
    session['command_history'].append({
        'command': command,
        'timestamp': datetime.utcnow().isoformat()
    })
    
    # Process command
    if command == 'start':
        # Implementation for start command
        pass
    elif command == 'stop':
        # Implementation for stop command
        pass
    
    return {
        'status': 'success',
        'history': session['command_history'],
        'ttl_remaining': session.ttl_remaining
    }
```

### Managing Sessions

```python
# Get session information
session = session_manager.get(session_id)
if session:
    print(f"Session TTL remaining: {session.ttl_remaining} seconds")
    print(f"Session data: {session.data}")

# Refresh session TTL
session_manager.refresh(session_id)

# End session
session_manager.end_session(session_id)
```

### Using Connection Pooling

```python
# Using context manager for automatic connection management
async with connection_pool.connection(vm_id) as conn:
    result1 = await conn.execute_command('get_system_info')
    result2 = await conn.execute_command('start_vm')
    # Connection is automatically returned to the pool
```

## Best Practices

1. **Session Management**
   - Always set appropriate TTL values based on your use case
   - Clean up sensitive data from sessions when no longer needed
   - Use descriptive session keys to avoid naming conflicts

2. **Connection Pooling**
   - Size the connection pool appropriately for your workload
   - Monitor pool usage and adjust settings as needed
   - Always release connections back to the pool when done

3. **Error Handling**
   - Implement proper error handling for session and connection operations
   - Handle session expiration gracefully
   - Log connection pool statistics for monitoring

## Troubleshooting

### Common Issues

1. **Session Expiration**
   - **Symptom**: Sessions expire too quickly
   - **Solution**: Increase the TTL value when creating the session manager

2. **Connection Leaks**
   - **Symptom**: Running out of available connections
   - **Solution**: Ensure all connections are properly released using try/finally or context managers

3. **Performance Issues**
   - **Symptom**: High latency with stateful operations
   - **Solution**: Monitor connection pool metrics and adjust pool size and TTL values

## Performance Considerations

1. **Session Storage**
   - For single-node deployments, in-memory storage is sufficient
   - For distributed deployments, consider using Redis or another distributed cache

2. **Connection Pool Tuning**
   - Monitor connection pool metrics to determine optimal pool size
   - Adjust TTL values based on your workload patterns

3. **Monitoring**
   - Track session creation and expiration rates
   - Monitor connection pool utilization
   - Set up alerts for abnormal conditions



