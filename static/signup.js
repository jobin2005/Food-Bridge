function validatePassword() {
    var password = document.getElementById("password");
    var passwordError = document.getElementById("passwordError");

    var passwordPattern = /^(?=.[!@#$%^&(),.?\":{}|<>])[A-Za-z\d!@#$%^&*(),.?\":{}|<>]{6,}$/;

    if (!passwordPattern.test(password.value)) {
      passwordError.style.display = "block";
    } else {
      passwordError.style.display = "none";
    }
  }

  function validateConfirmPassword() {
    var password = document.getElementById("password");
    var confirmPassword = document.getElementById("confirm_password");
    var passwordMatchError = document.getElementById("passwordMatchError");

    if (password.value !== confirmPassword.value) {
      passwordMatchError.style.display = "block";
    } else {
      passwordMatchError.style.display = "none";
    }
  }
  async function register() {
    const username = document.getElementById("regname").value.trim();
    const password = document.getElementById("password").value.trim();
    const confirmPassword = document.getElementById("confirm_password").value.trim();
    const email = document.querySelector("input[name='email']").value.trim();
    const role = document.querySelector("input[name='role']:checked")?.value;

    const passwordError = document.getElementById("passwordError");
    const passwordMatchError = document.getElementById("passwordMatchError");

    // ✅ Check if passwords match
    if (password !== confirmPassword) {
        passwordMatchError.style.display = "block";
        return;
    } else {
        passwordMatchError.style.display = "none";
    }

    // ✅ Validate required fields
    if (!username || !password || !email || !role) {
        alert("All fields are required!");
        return;
    }

    try {
        const response = await fetch("/register", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ username, password, email, role })
        });

        const result = await response.json();

        if (response.ok) {
            alert("✅ Registration successful! Redirecting to login.");
            window.location.href = "signup.html";  // ✅ Redirect to login page
        } else {
            alert(`❌ Error: ${result.error}`);
        }
    } catch (error) {
        console.error("❌ Fetch Error:", error);
        alert("Something went wrong. Check console for details.");
    }
}



async function login() {
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();
    const errorElement = document.getElementById("loginError");

    const response = await fetch("/login", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ username, password })
    });

    const result = await response.json();
    if (response.ok) {
        alert("Welcome!");
        window.location.href = "donor.html"; 
    } else {
        errorElement.textContent = result.error;
        errorElement.style.display = "block";
    }
}

