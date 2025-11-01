export async function load() {
	const response = await fetch('http://127.0.0.1:8000/sessions/');
	const sessions = await response.json();
	
	return {
		sessions
	};
}

