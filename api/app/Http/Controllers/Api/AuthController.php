<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\User;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Str;
use Illuminate\Validation\ValidationException;
use Illuminate\Support\Facades\DB;

class AuthController extends Controller
{
    public function register(Request $request)
    {
        $data = $request->validate([
            'name'              => 'required|string|max:255',
            'email'             => 'required|email|unique:core_users,email',
            'password'          => 'required|string|min:8|confirmed',
            'enterprise_id'     => 'nullable|uuid',
            'enterprise_name'   => 'nullable|string|max:255',
            'role'              => 'nullable|string',
        ]);

        // Résoudre l'enterprise_id : utiliser celui fourni, ou créer une entreprise par défaut
        $enterpriseId = $data['enterprise_id'] ?? null;

        if (!$enterpriseId) {
            // Réutiliser la première entreprise existante si possible
            $existing = DB::table('core_enterprises')->whereNull('deleted_at')->first();
            if ($existing) {
                $enterpriseId = $existing->id;
            } else {
                // Créer une entreprise par défaut
                $enterpriseId = (string) Str::uuid();
                DB::table('core_enterprises')->insert([
                    'id'         => $enterpriseId,
                    'name'       => $data['enterprise_name'] ?? 'Ayanna Solutions',
                    'currency'   => 'USD',
                    'created_at' => now(),
                    'updated_at' => now(),
                ]);
            }
        }

        $user = User::create([
            'name'          => $data['name'],
            'email'         => $data['email'],
            'password'      => $data['password'],   // le cast 'hashed' du modele hashera automatiquement
            'enterprise_id' => $enterpriseId,
            'role'          => $data['role'] ?? 'admin',
        ]);

        $token = $user->createToken('api-token')->plainTextToken;

        return response()->json(['user' => $user, 'token' => $token], 201);
    }

    public function login(Request $request)
    {
        $request->validate([
            'email'    => 'required|email',
            'password' => 'required|string',
        ]);

        $user = User::where('email', $request->email)->first();

        if (! $user || ! Hash::check($request->password, $user->password)) {
            throw ValidationException::withMessages([
                'email' => ['Les identifiants sont incorrects.'],
            ]);
        }

        $token = $user->createToken('api-token')->plainTextToken;

        return response()->json(['user' => $user, 'token' => $token]);
    }

    public function logout(Request $request)
    {
        $request->user()->currentAccessToken()->delete();
        return response()->json(['message' => 'Déconnecté avec succès.']);
    }

    public function me(Request $request)
    {
        return response()->json($request->user()->load('enterprise'));
    }
}
