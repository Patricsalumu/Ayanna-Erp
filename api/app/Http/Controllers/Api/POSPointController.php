<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\POSPoint;
use Illuminate\Http\Request;

class POSPointController extends Controller
{
    public function index()   { return response()->json(POSPoint::withTrashed()->paginate(50)); }
    public function show($id) { return response()->json(POSPoint::withTrashed()->with('enterprise')->findOrFail($id)); }
    public function store(Request $r) { return response()->json(POSPoint::create($r->all()), 201); }
    public function update(Request $r, $id) { $m = POSPoint::withTrashed()->findOrFail($id); $m->update($r->all()); return response()->json($m); }
    public function destroy($id) { POSPoint::findOrFail($id)->delete(); return response()->json(['message' => 'Supprimé.']); }
}
