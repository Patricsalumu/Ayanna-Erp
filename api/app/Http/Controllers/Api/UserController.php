<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\User;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;

class UserController extends Controller
{
    public function index()       { return response()->json(User::withTrashed()->latest()->paginate(50)); }
    public function show($id)     { return response()->json(User::withTrashed()->findOrFail($id)); }

    public function store(Request $request)
    {
        $data = $request->validate([
            'id'            => 'nullable|uuid',
            'name'          => 'required|string',
            'email'         => 'required|email|unique:users,email',
            'password'      => 'required|string|min:6',
            'enterprise_id' => 'nullable|uuid',
            'pos_id'        => 'nullable|uuid',
            'role'          => 'nullable|string',
        ]);
        $data['password'] = Hash::make($data['password']);
        return response()->json(User::create($data), 201);
    }

    public function update(Request $request, $id)
    {
        $user = User::withTrashed()->findOrFail($id);
        $payload = $request->except('password');
        if ($request->filled('password')) {
            $payload['password'] = Hash::make($request->password);
        }
        $user->update($payload);
        return response()->json($user);
    }

    public function destroy($id)
    {
        User::findOrFail($id)->delete();
        return response()->json(['message' => 'Supprimé.']);
    }
}
