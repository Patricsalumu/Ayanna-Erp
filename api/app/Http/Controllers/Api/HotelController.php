<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\HotelCategory;
use App\Models\HotelRoom;
use App\Models\HotelReservation;
use Illuminate\Http\Request;

class HotelCategoryController extends Controller
{
    public function index()   { return response()->json(HotelCategory::withTrashed()->with('rooms')->paginate(50)); }
    public function show($id) { return response()->json(HotelCategory::withTrashed()->findOrFail($id)); }
    public function store(Request $r)  { return response()->json(HotelCategory::create($r->all()), 201); }
    public function update(Request $r, $id) { $m = HotelCategory::withTrashed()->findOrFail($id); $m->update($r->all()); return response()->json($m); }
    public function destroy($id) { HotelCategory::findOrFail($id)->delete(); return response()->json(['message' => 'Supprimé.']); }
}

class HotelRoomController extends Controller
{
    public function index(Request $r)
    {
        $q = HotelRoom::withTrashed()->with('category');
        if ($r->filled('pos_id')) $q->where('pos_id', $r->pos_id);
        if ($r->filled('statut')) $q->where('statut', $r->statut);
        return response()->json($q->paginate(100));
    }
    public function show($id) { return response()->json(HotelRoom::withTrashed()->with(['category','reservations'])->findOrFail($id)); }
    public function store(Request $r)  { return response()->json(HotelRoom::create($r->all()), 201); }
    public function update(Request $r, $id) { $m = HotelRoom::withTrashed()->findOrFail($id); $m->update($r->all()); return response()->json($m); }
    public function destroy($id) { HotelRoom::findOrFail($id)->delete(); return response()->json(['message' => 'Supprimé.']); }
}

class HotelReservationController extends Controller
{
    public function index(Request $r)
    {
        $q = HotelReservation::withTrashed()->with(['room.category','user','paiements']);
        if ($r->filled('pos_id')) $q->where('pos_id', $r->pos_id);
        if ($r->filled('statut')) $q->where('statut', $r->statut);
        return response()->json($q->latest('date_arrivee')->paginate(50));
    }
    public function show($id) { return response()->json(HotelReservation::withTrashed()->with(['room.category','user','paiements.paymentMode'])->findOrFail($id)); }
    public function store(Request $r)  { return response()->json(HotelReservation::create($r->all()), 201); }
    public function update(Request $r, $id) { $m = HotelReservation::withTrashed()->findOrFail($id); $m->update($r->all()); return response()->json($m); }
    public function destroy($id) { HotelReservation::findOrFail($id)->delete(); return response()->json(['message' => 'Supprimé.']); }
}
