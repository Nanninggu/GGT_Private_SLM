# 개별 메시지

**생성 시간:** 21:56:36

## 🤖 AI 어시스턴트

## Rust 채팅 프로그램 서버 및 클라이언트 구현 안내

**목표**: 서버와 클라이언트 간의 간단한 텍스트 채팅 프로그램을 Rust로 구축합니다. 이 구현은 TCP 소켓 프로그래밍을 기반으로 합니다.

### 서버 구현 (Server)

서버는 특정 주소에서 클라이언트 연결을 수락하고, 수신된 메시지를 모든 연결된 클라이언트에게 전송하는 역할을 합니다.

**코드 예시:**
```rust
use std::net::{IpAddr, Ipv4Addr, Ipv6Addr, SocketAddr};
use std::sync::mpsc::{self, Receiver}; // 메시지 브로드캐스트 채널 사용
use std::thread; // 비동기 처리를 위한 스레드 활용
use std::collections::HashMap; // 클라이언트 관리용 해시맵

fn main() {
    // 서버 주소 설정 (예: localhost:8080)
    let addr = SocketAddr::from(IpAddr::V4("127.0.0.1".parse().unwrap(), 8080));

    println!("서버가 {}에서 시작합니다", addr);

    // 메시지 전송 채널 생성
    let (tx, rx) = mpsc::channel(); // 메시지 브로드캐스트 채널

    // 클라이언트 연결 수락 스레드 시작
    let handle = thread::spawn(move || {
        let mut listeners = Vec::new(); // 연결된 클라이언트 저장용 벡터
        loop {
            match std::net::TcpListener::bind(addr).unwrap() { // 클라이언트 연결 수락
                Ok((sock, _)) => {
                    listeners.push(sock); // 연결된 소켓 추가
                    handle_client(sock, tx); // 각 클라이언트 처리 함수 호출
                }
                Err(e) => {
                    eprintln!("클라이언트 연결 실패: {}", e);
                    drop(tx); // 채널 드롭하여 스레드 종료 시도
                    return;
                }
            }
        }
    });

    // 메시지 브로드캐스트 로직
    let mut clients = HashMap::new(); // 클라이언트 주소와 트랜잭션 매핑
    loop {
        match rx.recv() { // 메시지 수신
            Ok(msg) => {
                println!("전송된 메시지: {}", msg);
                broadcast_message(&clients, msg); // 모든 클라이언트에게 브로드캐스트
            }
            Err(_) => break, // 수신 채널 종료 시 루프 종료
        }
    }

    // 클라이언트 연결 종료 대기 (실제로는 무한 루프 내에서 처리됨)
    handle.join().expect("스레드 종료 실패");
}

fn handle_client(socket: std::net::TcpStream, tx: mpsc::Sender<String>) {
    let mut buffer = [0; 1024]; // 메시지 수신 버퍼
    loop {
        match socket.read(&mut buffer) {
            Ok(n) if n == 0 => println!("클라이언트 연결 종료"), break; // 연결 종료 시 루프 종료
            Ok(n) => {
                let msg = String::from_utf8_lossy(&buffer[..n]).into_owned(); // 메시지 추출
                println!("받은 메시지: {}", msg); // 수신 메시지 출력
                tx.send(msg).expect("메시지 전송 실패"); // 서버로 브로드캐스트 요청 전송
            }
            Err(e) => println!("연결 오류: {}", e), break; // 오류 처리 및 종료
        }
    }
}

fn broadcast_message(clients: &HashMap<SocketAddr, mpsc::Receiver<String>>, msg: String) {
    for (_, rx) in clients.iter() {
        if let Err(_) = rx.send(msg).await { // 클라이언트에게 메시지 전송 시도
            println!("클라이언트 연결 종료");
        }
    }
}
```

### 클라이언트 구현 (Client)

클라이언트는 서버와 연결하여 메시지를 주고받습니다. 서버로부터 메시지를 수신하고, 필요할 때 서버에 브로드캐스트 요청을 보냅니다.

**코드 예시:**
```rust
use std::net::{IpAddr, Ipv4Addr, Ipv6Addr, SocketAddr};
use std::thread; // 비동기 처리를 위한 스레드 활용
use std::time::Duration;
use std::io::{self, Read}; // 입출력 처리
use std::sync::mpsc::Receiver; // 메시지 수신 채널 사용

fn main() {
    // 서버 주소 설정 (예: localhost:8080)
    let addr = "127.0.0.1:8080".parse().unwrap();

    println!("서버 {}에 연결 중입니다", addr);

    // 소켓 생성 및 연결 시도
    let mut sock = match std::net::TcpStream::connect(addr) {
        Ok(sock) => sock,
        Err(e) => {
            eprintln!("연결 실패: {}", e);
            return;
        }
    };

    // 메시지 수신 및 전송 루프
    loop {
        let mut buffer = [0; 1024]; // 메시지 수신 버퍼
        match sock.read(&mut buffer) {
            Ok(n) if n == 0 => println!("서버 연결 종료"), break; // 연결 종료 시 루프 종료
            Ok(n) => {
                let msg = String::from_utf8_lossy(&buffer[..n]).into_owned(); // 메시지 추출
                println!("받은 메시지: {}", msg); // 수신 메시지 출력
                if let Err(e) = sock.send_all(b"BroadcastMessage\n") { // 서버에 브로드캐스트 요청 전송
                    eprintln!("메시지 전송 실패: {}", e);
                }
            }
            Err(e) => println!("읽기 오류: {}", e), break; // 오류 처리 및 종료
        }
    }
}
```

### 설명 요약

1. **서버**:
   - `SocketAddr`를 통해 서버 주소를 설정합니다.
   - `TcpListener`을 사용해 클라이언트 연결을 수락하고, 각 클라이언트와의 통신은 별도 스레드에서 처리됩니다.
   - `mpsc::channel`을 이용해 메시지 브로드캐스트 채널을 생성하여 모든 연결된 클라이언트에게 메시지를 전송합니다.

2. **클라이언트**:
   - 서버 주소로 연결을 시도하고, 성공 시 메시지 수신 및 전송 루프를 실행합니다.
   - 수신한 메시지는 콘솔에 출력되며, 필요하면 서버에 브로드캐스트 요청을 보냅니다 (서버 구현에서 처리됨).

### 주의사항
- 실제 환경에서는 보안 강화 (예: TLS 사용), 더 정교한 에러 핸들링, 그리고 성능 최적화를 고려해야 합니다.
- 위 코드는 간단한 예시이므로 실제 사용 시에는 추가적인 기능과 안정성 향상이 필요합니다.

