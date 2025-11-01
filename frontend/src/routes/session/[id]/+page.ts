export async function load({ params }) {
	const id = params.id;
	const response = await fetch(`http://127.0.0.1:8000/session/${id}`);
	const steps = await response.json();
	
	return {
		steps,
		id
	};
}

